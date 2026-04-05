# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Unit tests for core/components.py — all 32 Aetheris components.

Verifies instantiation, calculate_asymptotes, metadata properties,
and physics behaviors for every component across Phases A-D.
"""
import pytest
import numpy as np
from core.components import (
    # Phase A
    AetherGauge, AetherSparkline, AetherBarGroup, AetherStatusOrb,
    AetherHeatMap, AetherKineticToggle, AetherRadialProgress, AetherValueMetric,
    # Phase B
    AetherWindow, AetherSideNav, AetherToolbar, AetherModal,
    AetherSplitter, AetherScrollPanel, AetherContextMenu, AetherTooltipBox,
    # Phase C
    AetherHero, AetherPricingCard, AetherNavbar, AetherToastAlert,
    AetherAccordionItem, AetherDrawer, AetherTabs, AetherPillBadge,
    # Phase D
    AetherSpringBox, AetherAttractor, AetherBoundary, AetherSurface,
    AetherBouncyLabel, AetherMagnetLink, AetherPhysicsDivider, AetherTeleport,
)
from core.elements import StaticBox


# =============================================================================
# Phase A: Dashboard Components
# =============================================================================

class TestAetherGauge:
    def test_init_defaults(self):
        g = AetherGauge(value=50, min_val=0, max_val=100)
        assert g.value == 50
        assert g.normalized_value() == pytest.approx(0.5)
        assert g._element_type == "aether_gauge"

    def test_value_clamping(self):
        g = AetherGauge(min_val=0, max_val=100)
        g.value = 150
        assert g.value == 100
        g.value = -10
        assert g.value == 0

    def test_asymptotes_static(self):
        g = AetherGauge(x=10, y=20, w=120, h=120)
        result = g.calculate_asymptotes(800, 600)
        assert np.allclose(result, [10, 20, 120, 120])

    def test_metadata(self):
        g = AetherGauge(value=75, min_val=0, max_val=100, label="CPU")
        meta = g.gauge_metadata
        assert meta["value"] == 75
        assert meta["label"] == "CPU"
        assert meta["normalized"] == pytest.approx(0.75)


class TestAetherSparkline:
    def test_init_and_push(self):
        s = AetherSparkline(data=[1, 2, 3])
        assert len(s.data) == 3
        s.push_value(4)
        assert len(s.data) == 4

    def test_data_capped_at_64(self):
        s = AetherSparkline()
        for i in range(100):
            s.push_value(float(i))
        assert len(s.data) == 64

    def test_metadata(self):
        s = AetherSparkline(data=[10, 20, 30], label="Revenue")
        meta = s.sparkline_metadata
        assert meta["min"] == 10
        assert meta["max"] == 30
        assert meta["label"] == "Revenue"


class TestAetherBarGroup:
    def test_init(self):
        bg = AetherBarGroup(values=[10, 20, 30], labels=["A", "B", "C"])
        assert len(bg._values) == 3
        meta = bg.bar_metadata
        assert meta["bar_count"] == 3

    def test_set_values(self):
        bg = AetherBarGroup()
        bg.set_values([5, 15, 25])
        assert bg._values == [5.0, 15.0, 25.0]


class TestAetherStatusOrb:
    def test_init_ok(self):
        orb = AetherStatusOrb(status="ok")
        assert orb.status == "ok"
        assert orb._color[0] == pytest.approx(0.2)

    def test_status_change(self):
        orb = AetherStatusOrb(status="ok")
        orb.status = "critical"
        assert orb.status == "critical"
        assert orb._color[0] == pytest.approx(0.9)

    def test_metadata(self):
        orb = AetherStatusOrb(status="warning", pulse_frequency=2.0, label="DB")
        meta = orb.orb_metadata
        assert meta["pulse_frequency"] == 2.0
        assert meta["status"] == "warning"


class TestAetherHeatMap:
    def test_init(self):
        hm = AetherHeatMap(rows=3, cols=4)
        assert hm._data.shape == (3, 4)

    def test_normalized_data(self):
        hm = AetherHeatMap(rows=2, cols=2, data=[[0, 50], [100, 150]])
        norm = hm.normalized_data()
        assert norm.min() == pytest.approx(0.0)
        assert norm.max() == pytest.approx(1.0)

    def test_set_data(self):
        hm = AetherHeatMap(rows=2, cols=2)
        hm.set_data([[1, 2], [3, 4]])
        assert hm._data.shape == (2, 2)


class TestAetherKineticToggle:
    def test_init_off(self):
        t = AetherKineticToggle(is_on=False)
        assert t.is_on is False
        assert t._knob_ratio == 0.0

    def test_toggle(self):
        t = AetherKineticToggle(is_on=False)
        t.toggle()
        assert t.is_on is True
        assert t._knob_ratio == 1.0
        t.toggle()
        assert t.is_on is False


class TestAetherRadialProgress:
    def test_init(self):
        rp = AetherRadialProgress(progress=0.75)
        assert rp.progress == pytest.approx(0.75)

    def test_progress_clamping(self):
        rp = AetherRadialProgress()
        rp.progress = 1.5
        assert rp.progress == 1.0
        rp.progress = -0.5
        assert rp.progress == 0.0


class TestAetherValueMetric:
    def test_formatted_value(self):
        m = AetherValueMetric(value=1500)
        assert m.formatted_value() == "1.5K"
        m.value = 2500000
        assert m.formatted_value() == "2.5M"
        m.value = 3_500_000_000
        assert m.formatted_value() == "3.5B"

    def test_metadata(self):
        m = AetherValueMetric(value=42, unit="USD", label="Revenue", trend=5.2)
        meta = m.metric_metadata
        assert meta["trend"] == 5.2
        assert meta["unit"] == "USD"


# =============================================================================
# Phase B: Desktop Components
# =============================================================================

class TestAetherWindow:
    def test_init(self):
        w = AetherWindow(title="Main", resizable=False)
        meta = w.window_metadata
        assert meta["title"] == "Main"
        assert meta["resizable"] is False


class TestAetherSideNav:
    def test_left_closed(self):
        nav = AetherSideNav(position="left", is_open=False, w=250)
        result = nav.calculate_asymptotes(1280, 720)
        assert result[0] == pytest.approx(-250)

    def test_left_open(self):
        nav = AetherSideNav(position="left", is_open=True, w=250)
        result = nav.calculate_asymptotes(1280, 720)
        assert result[0] == pytest.approx(0)

    def test_toggle(self):
        nav = AetherSideNav(is_open=False)
        nav.toggle()
        assert nav._is_open is True


class TestAetherToolbar:
    def test_add_item(self):
        tb = AetherToolbar()
        tb.add_item("Save", "💾")
        assert len(tb._items) == 1
        assert tb._items[0]["label"] == "Save"


class TestAetherModal:
    def test_hidden(self):
        m = AetherModal(is_visible=False)
        result = m.calculate_asymptotes(1280, 720)
        assert result[2] == pytest.approx(0.0)
        assert result[3] == pytest.approx(0.0)

    def test_visible_centers(self):
        m = AetherModal(w=500, h=350, is_visible=True)
        result = m.calculate_asymptotes(1280, 720)
        assert result[0] == pytest.approx((1280 - 500) / 2)
        assert result[1] == pytest.approx((720 - 350) / 2)

    def test_show_hide(self):
        m = AetherModal()
        m.show()
        assert m._is_visible is True
        m.hide()
        assert m._is_visible is False


class TestAetherSplitter:
    def test_ratio_clamping(self):
        sp = AetherSplitter(ratio=0.5)
        sp.ratio = 0.95
        assert sp.ratio == pytest.approx(0.9)
        sp.ratio = 0.01
        assert sp.ratio == pytest.approx(0.1)


class TestAetherScrollPanel:
    def test_scroll_clamping(self):
        sp = AetherScrollPanel(h=300, content_h=600)
        sp.scroll_to(400)
        assert sp._scroll_y == pytest.approx(300)
        sp.scroll_to(-10)
        assert sp._scroll_y == pytest.approx(0)


class TestAetherContextMenu:
    def test_add_item(self):
        cm = AetherContextMenu()
        cm.add_item("Copy", "Ctrl+C")
        assert len(cm._items) == 1

    def test_hidden_collapses(self):
        cm = AetherContextMenu(x=100, y=100, w=200, h=150, is_visible=False)
        result = cm.calculate_asymptotes(1280, 720)
        assert result[2] == pytest.approx(0.0)


class TestAetherTooltipBox:
    def test_follow_target(self):
        tt = AetherTooltipBox(target_x=100, target_y=200, offset_y=-10, w=150, h=40)
        result = tt.calculate_asymptotes(1280, 720)
        assert result[0] == pytest.approx(100 - 75)
        assert result[1] == pytest.approx(200 - 10 - 40)


# =============================================================================
# Phase C: Web Components
# =============================================================================

class TestAetherHero:
    def test_full_width(self):
        h = AetherHero()
        result = h.calculate_asymptotes(1280, 720)
        assert result[2] == pytest.approx(1280)


class TestAetherPricingCard:
    def test_hover_scale(self):
        pc = AetherPricingCard(x=100, y=100, w=300, h=400)
        pc.set_hover(True)
        result = pc.calculate_asymptotes(1280, 720)
        assert result[2] == pytest.approx(300 * 1.05)
        assert result[3] == pytest.approx(400 * 1.05)

    def test_no_hover(self):
        pc = AetherPricingCard(w=300, h=400)
        pc.set_hover(False)
        result = pc.calculate_asymptotes(1280, 720)
        assert result[2] == pytest.approx(300)


class TestAetherNavbar:
    def test_sticky(self):
        nb = AetherNavbar(is_sticky=True)
        result = nb.calculate_asymptotes(1280, 720)
        assert result[1] == pytest.approx(0.0)
        assert result[2] == pytest.approx(1280)


class TestAetherToastAlert:
    def test_visible_position(self):
        toast = AetherToastAlert(w=350, h=60, message="Hello")
        result = toast.calculate_asymptotes(1280, 720)
        assert result[0] == pytest.approx(1280 - 350 - 20)

    def test_expired_offscreen(self):
        toast = AetherToastAlert(message="Hello", duration=0.001)
        toast.tick(1.0)
        result = toast.calculate_asymptotes(1280, 720)
        assert result[0] > 1280

    def test_metadata_remaining(self):
        toast = AetherToastAlert(message="Hi", duration=5.0)
        toast.tick(2.0)
        meta = toast.toast_metadata
        assert meta["remaining"] == pytest.approx(3.0, abs=0.1)


class TestAetherAccordionItem:
    def test_collapsed(self):
        acc = AetherAccordionItem(h=50, expanded_h=200, is_expanded=False)
        result = acc.calculate_asymptotes(1280, 720)
        assert result[3] == pytest.approx(50)

    def test_expanded(self):
        acc = AetherAccordionItem(h=50, expanded_h=200, is_expanded=True)
        result = acc.calculate_asymptotes(1280, 720)
        assert result[3] == pytest.approx(200)

    def test_toggle(self):
        acc = AetherAccordionItem(is_expanded=False)
        acc.toggle()
        assert acc._is_expanded is True


class TestAetherDrawer:
    def test_left_closed(self):
        d = AetherDrawer(position="left", w=300, is_open=False)
        result = d.calculate_asymptotes(1280, 720)
        assert result[0] == pytest.approx(-300)

    def test_right_open(self):
        d = AetherDrawer(position="right", w=300, is_open=True)
        result = d.calculate_asymptotes(1280, 720)
        assert result[0] == pytest.approx(1280 - 300)


class TestAetherTabs:
    def test_active_indicator(self):
        tabs = AetherTabs(w=600, tabs=["A", "B", "C"], active_index=1)
        meta = tabs.tabs_metadata
        tab_w = 600 / 3
        assert meta["indicator_x"] == pytest.approx(tab_w)
        assert meta["indicator_w"] == pytest.approx(tab_w)

    def test_set_active_clamped(self):
        tabs = AetherTabs(tabs=["A", "B"])
        tabs.set_active(10)
        assert tabs._active_index == 1


class TestAetherPillBadge:
    def test_anchor_top_right(self):
        parent = StaticBox(x=100, y=100, w=200, h=100)
        pill = AetherPillBadge(w=24, h=24, parent=parent, anchor="top-right")
        result = pill.calculate_asymptotes(1280, 720)
        assert result[0] == pytest.approx(100 + 200 - 12)
        assert result[1] == pytest.approx(100 - 12)

    def test_no_parent_static(self):
        pill = AetherPillBadge(x=50, y=50, w=24, h=24)
        result = pill.calculate_asymptotes(1280, 720)
        assert np.allclose(result, [50, 50, 24, 24])


# =============================================================================
# Phase D: Core Physics Utilities
# =============================================================================

class TestAetherSpringBox:
    def test_init(self):
        sb = AetherSpringBox(spring_k=20.0, damping_c=3.0)
        meta = sb.spring_box_metadata
        assert meta["spring_k"] == 20.0
        assert meta["damping_c"] == 3.0


class TestAetherAttractor:
    def test_force_within_radius(self):
        att = AetherAttractor(x=100, y=100, strength=100, radius=200)
        force = att.force_on(50, 50)
        magnitude = np.sqrt(force[0]**2 + force[1]**2)
        assert magnitude > 0

    def test_force_outside_radius(self):
        att = AetherAttractor(x=0, y=0, strength=1, radius=10)
        force = att.force_on(100, 100)
        assert np.allclose(force, [0, 0])


class TestAetherBoundary:
    def test_clamp_inside(self):
        b = AetherBoundary(x=0, y=0, w=800, h=600, clamp_inside=True)
        result = b.clamp_point(900, 700, 50, 50)
        assert result[0] == pytest.approx(750)
        assert result[1] == pytest.approx(550)

    def test_no_clamp_outside(self):
        b = AetherBoundary(clamp_inside=False)
        result = b.clamp_point(900, 700, 50, 50)
        assert result[0] == pytest.approx(900)


class TestAetherSurface:
    def test_friction(self):
        s = AetherSurface(friction=0.3)
        result = s.apply_friction(10, 10)
        assert result[0] == pytest.approx(7.0)
        assert result[1] == pytest.approx(7.0)


class TestAetherBouncyLabel:
    def test_text_change_triggers_bounce(self):
        lbl = AetherBouncyLabel(text="Hello")
        assert lbl._bounce_amplitude == 0.0
        lbl.text = "World"
        assert lbl._bounce_amplitude == pytest.approx(8.0)

    def test_bounce_decay(self):
        lbl = AetherBouncyLabel(text="Hello")
        lbl.text = "World"
        lbl.tick_bounce(1.0)
        assert lbl._bounce_amplitude < 8.0


class TestAetherMagnetLink:
    def test_should_snap(self):
        m = AetherMagnetLink(x=100, y=100, w=50, h=50, snap_distance=20)
        assert m.should_snap(105, 105, 50, 50)
        assert not m.should_snap(500, 500, 50, 50)


class TestAetherPhysicsDivider:
    def test_preferred_size(self):
        d = AetherPhysicsDivider(preferred_size=40, min_size=10, w=100)
        result = d.calculate_asymptotes(1280, 720)
        assert result[2] == pytest.approx(40)

    def test_min_size_enforced(self):
        d = AetherPhysicsDivider(preferred_size=40, min_size=10, w=5)
        result = d.calculate_asymptotes(1280, 720)
        assert result[2] == pytest.approx(10)


class TestAetherTeleport:
    def test_blend_interpolation(self):
        tp = AetherTeleport(
            state_a={"x": 0, "y": 0},
            state_b={"x": 100, "y": 100},
            blend=0.5,
        )
        blended = tp.blended_state()
        assert blended["x"] == pytest.approx(50)
        assert blended["y"] == pytest.approx(50)

    def test_teleport_to_b(self):
        tp = AetherTeleport(state_a={"v": 0}, state_b={"v": 100}, blend=0.0)
        tp.teleport_to_b()
        assert tp._blend == 1.0
        assert tp.blended_state()["v"] == pytest.approx(100)

    def test_teleport_to_a(self):
        tp = AetherTeleport(state_a={"v": 0}, state_b={"v": 100}, blend=1.0)
        tp.teleport_to_a()
        assert tp._blend == 0.0
        assert tp.blended_state()["v"] == pytest.approx(0.0)
