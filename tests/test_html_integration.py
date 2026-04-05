# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
HTML → Component Integration Tests.

Verifies that HTML attributes are correctly extracted, type-converted,
and hydrated into fully functional Aetheris components through the
full pipeline: HTML/CSS → AetherHTMLParser → UIBuilder → Engine.
"""
import pytest
import numpy as np
from core.engine import AetherEngine
from core.ui_builder import UIBuilder
from core.html_parser import AetherHTMLParser


class TestHTMLAttributeExtraction:
    """Verify _parse_val correctly converts HTML attributes."""

    def setup_method(self):
        self.parser = AetherHTMLParser()

    def test_numeric_value_attr(self):
        html = '<aether-gauge id="cpu" value="85" min_val="0" max_val="100"></aether-gauge>'
        result = self.parser.parse(html)
        elem = result['elements'][0]
        assert elem['value'] == 85
        assert elem['min_val'] == 0
        assert elem['max_val'] == 100

    def test_float_attr(self):
        html = '<aether-spring-box id="box" spring_k="15.5" damping_c="2.3"></aether-spring-box>'
        result = self.parser.parse(html)
        elem = result['elements'][0]
        assert elem['spring_k'] == pytest.approx(15.5)
        assert elem['damping_c'] == pytest.approx(2.3)

    def test_boolean_true_attr(self):
        html = '<aether-toggle id="toggle" is_on="true"></aether-toggle>'
        result = self.parser.parse(html)
        elem = result['elements'][0]
        assert elem['is_on'] is True

    def test_boolean_false_attr(self):
        html = '<aether-modal id="modal" is_visible="false"></aether-modal>'
        result = self.parser.parse(html)
        elem = result['elements'][0]
        assert elem['is_visible'] is False

    def test_string_attr(self):
        html = '<aether-status-orb id="orb" status="critical" label="DB"></aether-status-orb>'
        result = self.parser.parse(html)
        elem = result['elements'][0]
        assert elem['status'] == 'critical'
        assert elem['label'] == 'DB'

    def test_reserved_attrs_excluded(self):
        html = '<aether-gauge id="g1" class="widget" style="color:red" value="50"></aether-gauge>'
        result = self.parser.parse(html)
        elem = result['elements'][0]
        assert 'class' not in elem
        assert 'style' not in elem
        assert elem['value'] == 50


class TestHTMLToComponentHydration:
    """Full pipeline: HTML string → UIBuilder → Engine → verify component properties."""

    def _build(self, html, css=''):
        engine = AetherEngine()
        builder = UIBuilder()
        count = builder.build_from_html(engine, html, css)
        return engine, builder, count

    def test_gauge_hydration(self):
        html = '<aether-gauge id="cpu" value="85" min_val="0" max_val="100" label="CPU"></aether-gauge>'
        engine, builder, count = self._build(html)
        assert count == 1
        gauge = builder._element_refs['cpu']
        assert gauge.value == 85
        assert gauge._min_val == 0
        assert gauge._max_val == 100
        assert gauge._label == 'CPU'
        assert gauge.normalized_value() == pytest.approx(0.85)

    def test_toggle_hydration(self):
        html = '<aether-toggle id="dm" is_on="true" label="Dark Mode"></aether-toggle>'
        engine, builder, count = self._build(html)
        assert count == 1
        toggle = builder._element_refs['dm']
        assert toggle.is_on is True
        assert toggle._label == 'Dark Mode'

    def test_spring_box_hydration(self):
        html = '<aether-spring-box id="sb" spring_k="20" damping_c="3.5"></aether-spring-box>'
        engine, builder, count = self._build(html)
        assert count == 1
        sb = builder._element_refs['sb']
        assert sb._spring_k == pytest.approx(20.0)
        assert sb._damping_c == pytest.approx(3.5)

    def test_status_orb_hydration(self):
        html = '<aether-status-orb id="api" status="warning" pulse_frequency="2.0" label="API"></aether-status-orb>'
        engine, builder, count = self._build(html)
        assert count == 1
        orb = builder._element_refs['api']
        assert orb.status == 'warning'
        assert orb._pulse_frequency == pytest.approx(2.0)

    def test_radial_progress_hydration(self):
        html = '<aether-radial-progress id="up" progress="0.75" label="Upload"></aether-radial-progress>'
        engine, builder, count = self._build(html)
        assert count == 1
        rp = builder._element_refs['up']
        assert rp.progress == pytest.approx(0.75)

    def test_value_metric_hydration(self):
        html = '<aether-value-metric id="rev" value="2500000" unit="USD" trend="12.5" label="Revenue"></aether-value-metric>'
        engine, builder, count = self._build(html)
        assert count == 1
        m = builder._element_refs['rev']
        assert m._value == pytest.approx(2500000)
        assert m._unit == 'USD'
        assert m._trend == pytest.approx(12.5)

    def test_modal_hydration(self):
        html = '<aether-modal id="confirm" title="Confirm" is_visible="true"></aether-modal>'
        engine, builder, count = self._build(html)
        assert count == 1
        modal = builder._element_refs['confirm']
        assert modal._title == 'Confirm'
        assert modal._is_visible is True

    def test_drawer_hydration(self):
        html = '<aether-drawer id="nav" is_open="true" position="right"></aether-drawer>'
        engine, builder, count = self._build(html)
        assert count == 1
        drawer = builder._element_refs['nav']
        assert drawer._is_open is True
        assert drawer._position == 'right'

    def test_tabs_hydration(self):
        html = '<aether-tabs id="tabs" active_index="0"></aether-tabs>'
        engine, builder, count = self._build(html)
        assert count == 1
        tabs = builder._element_refs['tabs']
        assert tabs._active_index == 0

    def test_attractor_hydration(self):
        html = '<aether-attractor id="grav" strength="500" radius="300"></aether-attractor>'
        engine, builder, count = self._build(html)
        assert count == 1
        att = builder._element_refs['grav']
        assert att._strength == pytest.approx(500.0)
        assert att._radius == pytest.approx(300.0)

    def test_teleport_hydration(self):
        html = '<aether-teleport id="tp" blend="0.5"></aether-teleport>'
        engine, builder, count = self._build(html)
        assert count == 1
        tp = builder._element_refs['tp']
        assert tp._blend == pytest.approx(0.5)

    def test_multiple_components_from_html(self):
        html = '''
        <aether-gauge id="cpu" value="72" min_val="0" max_val="100"></aether-gauge>
        <aether-toggle id="dark" is_on="false"></aether-toggle>
        <aether-status-orb id="db" status="ok"></aether-status-orb>
        '''
        engine, builder, count = self._build(html)
        assert count == 3
        assert builder._element_refs['cpu'].value == 72
        assert builder._element_refs['dark'].is_on is False
        assert builder._element_refs['db'].status == 'ok'


class TestNumericalStability:
    """Run 500 frames with HTML-hydrated components — no NaN/Inf allowed."""

    def test_500_frames_no_nan(self):
        html = '''
        <aether-gauge id="g1" value="85" min_val="0" max_val="100"></aether-gauge>
        <aether-spring-box id="sb1" spring_k="15" damping_c="2.5"></aether-spring-box>
        <aether-toggle id="t1" is_on="true"></aether-toggle>
        <aether-radial-progress id="rp1" progress="0.6"></aether-radial-progress>
        <aether-value-metric id="vm1" value="1500000" trend="5.2"></aether-value-metric>
        <aether-modal id="m1" is_visible="true"></aether-modal>
        <aether-drawer id="d1" is_open="true"></aether-drawer>
        <aether-accordion is_expanded="true" expanded_h="200"></aether-accordion>
        <aether-attractor id="att1" strength="100" radius="200"></aether-attractor>
        <aether-teleport id="tp1" blend="0.3"></aether-teleport>
        '''
        engine = AetherEngine()
        builder = UIBuilder()
        builder.build_from_html(engine, html)

        for i in range(500):
            data = engine.tick(1280, 720)
            assert not np.any(np.isnan(data['rect'])), f"NaN in rect at frame {i}"
            assert not np.any(np.isnan(data['color'])), f"NaN in color at frame {i}"
            assert not np.any(np.isinf(data['rect'])), f"Inf in rect at frame {i}"

    def test_gauge_value_change_during_simulation(self):
        html = '<aether-gauge id="cpu" value="50" min_val="0" max_val="100"></aether-gauge>'
        engine = AetherEngine()
        builder = UIBuilder()
        builder.build_from_html(engine, html)
        gauge = builder._element_refs['cpu']

        for _ in range(100):
            engine.tick(1280, 720)

        gauge.value = 90
        for _ in range(100):
            data = engine.tick(1280, 720)

        assert not np.any(np.isnan(data['rect']))
        assert gauge.value == 90
