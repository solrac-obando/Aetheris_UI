# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Audio Logic Tests — Mock audio provider verifies sound trigger evaluation
in AetherEngine without requiring actual audio hardware or files.
"""
import pytest
import numpy as np
from core.engine import AetherEngine
from core.ui_builder import UIBuilder
from core.audio_bridge import (
    AetherAudioBridge, MockAudioProvider,
    create_audio_bridge,
)
from core.elements import DifferentialElement, StaticBox


class TestMockAudioProvider:
    def test_play_sound_records(self):
        bridge = MockAudioProvider()
        bridge.play_sound('click', volume=0.8, pitch=1.0)
        assert len(bridge.history) == 1
        assert bridge.history[0]['sound_id'] == 'click'
        assert bridge.history[0]['volume'] == pytest.approx(0.8)

    def test_preload(self):
        bridge = MockAudioProvider()
        assert bridge.preload('ding', '/sounds/ding.ogg') is True

    def test_clear_history(self):
        bridge = MockAudioProvider()
        bridge.play_sound('a')
        bridge.play_sound('b')
        bridge.clear_history()
        assert len(bridge.history) == 0

    def test_stop_all_noop(self):
        bridge = MockAudioProvider()
        bridge.stop_all()
        assert len(bridge.history) == 0


class TestCreateAudioBridge:
    def test_mock_mode(self):
        bridge = create_audio_bridge(mode='mock')
        assert isinstance(bridge, MockAudioProvider)

    def test_web_mode(self):
        from core.audio_bridge import WebAudioProvider
        bridge = create_audio_bridge(mode='web')
        assert isinstance(bridge, WebAudioProvider)


class TestSoundTriggerEvaluation:
    """Test DifferentialElement.evaluate_sound_trigger() logic."""

    def test_no_trigger(self):
        elem = StaticBox(x=0, y=0, w=100, h=100)
        bridge = MockAudioProvider()
        result = elem.evaluate_sound_trigger(bridge)
        assert result is False
        assert len(bridge.history) == 0

    def test_impact_trigger_below_threshold(self):
        elem = StaticBox(x=0, y=0, w=100, h=100, sound_trigger='impact:5.0')
        elem.tensor.velocity = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        bridge = MockAudioProvider()
        result = elem.evaluate_sound_trigger(bridge)
        assert result is False

    def test_impact_trigger_crosses_threshold(self):
        elem = StaticBox(x=0, y=0, w=100, h=100, sound_trigger='impact:0.5')
        elem.tensor.velocity = np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32)
        elem._prev_velocity_mag = 0.0
        bridge = MockAudioProvider()
        elem.tensor.velocity = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        result = elem.evaluate_sound_trigger(bridge)
        assert result is True
        assert len(bridge.history) == 1
        assert bridge.history[0]['sound_id'] == 'impact'

    def test_settle_trigger(self):
        elem = StaticBox(x=0, y=0, w=100, h=100, sound_trigger='settle')
        elem.tensor.velocity = np.array([0.5, 0.0, 0.0, 0.0], dtype=np.float32)
        elem._prev_velocity_mag = 0.5
        bridge = MockAudioProvider()
        elem.tensor.velocity = np.array([0.01, 0.0, 0.0, 0.0], dtype=np.float32)
        result = elem.evaluate_sound_trigger(bridge)
        assert result is True
        assert bridge.history[0]['sound_id'] == 'settle'

    def test_collision_trigger(self):
        elem = StaticBox(x=0, y=0, w=100, h=100, sound_trigger='collision:wall_bounce')
        elem.tensor.acceleration = np.array([100.0, 0.0, 0.0, 0.0], dtype=np.float32)
        bridge = MockAudioProvider()
        result = elem.evaluate_sound_trigger(bridge)
        assert result is True
        assert bridge.history[0]['sound_id'] == 'wall_bounce'

    def test_multi_sound_trigger(self):
        elem = StaticBox(x=0, y=0, w=100, h=100,
                         sound_trigger='on:click_sound;off:release_sound')
        elem._prev_velocity_mag = 0.0
        elem.tensor.velocity = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        bridge = MockAudioProvider()
        result = elem.evaluate_sound_trigger(bridge)
        assert result is True
        assert bridge.history[0]['sound_id'] == 'click_sound'


class TestEngineAudioIntegration:
    """Full pipeline: HTML → Engine with audio bridge → verify triggers."""

    def test_engine_with_audio_bridge(self):
        html = '<aether-gauge id="g1" value="85" min_val="0" max_val="100" sound_trigger="impact:0.5"></aether-gauge>'
        engine = AetherEngine()
        bridge = MockAudioProvider()
        engine.audio_bridge = bridge
        builder = UIBuilder()
        builder.build_from_html(engine, html)
        gauge = builder._element_refs['g1']
        assert gauge.sound_trigger == 'impact:0.5'

    def test_engine_tick_evaluates_triggers(self):
        html = '<aether-toggle id="t1" is_on="true" sound_trigger="on:toggle_on;off:toggle_off"></aether-toggle>'
        engine = AetherEngine()
        bridge = MockAudioProvider()
        engine.audio_bridge = bridge
        builder = UIBuilder()
        builder.build_from_html(engine, html)
        toggle = builder._element_refs['t1']
        toggle._prev_velocity_mag = 0.0
        toggle.tensor.velocity = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        engine.tick(1280, 720)
        assert len(bridge.history) >= 1
        assert bridge.history[0]['sound_id'] == 'toggle_on'

    def test_engine_without_audio_bridge_no_crash(self):
        html = '<aether-gauge id="g1" value="50" sound_trigger="impact:0.5"></aether-gauge>'
        engine = AetherEngine()
        builder = UIBuilder()
        builder.build_from_html(engine, html)
        for _ in range(10):
            data = engine.tick(1280, 720)
        assert not np.any(np.isnan(data['rect']))

    def test_500_frames_with_audio_no_nan(self):
        html = '''
        <aether-gauge id="g1" value="85" sound_trigger="impact:0.5"></aether-gauge>
        <aether-toggle id="t1" is_on="true" sound_trigger="on:click;off:release"></aether-toggle>
        <aether-spring-box id="sb" spring_k="15" sound_trigger="collision:thud"></aether-spring-box>
        '''
        engine = AetherEngine()
        bridge = MockAudioProvider()
        engine.audio_bridge = bridge
        builder = UIBuilder()
        builder.build_from_html(engine, html)

        for i in range(500):
            data = engine.tick(1280, 720)
            assert not np.any(np.isnan(data['rect'])), f"NaN at frame {i}"
            assert not np.any(np.isnan(data['color'])), f"NaN at frame {i}"

    def test_missing_sound_file_no_crash(self):
        html = '<aether-gauge id="g1" value="50" sound_trigger="impact:0.5"></aether-gauge>'
        engine = AetherEngine()
        bridge = MockAudioProvider()
        engine.audio_bridge = bridge
        builder = UIBuilder()
        builder.build_from_html(engine, html)
        gauge = builder._element_refs['g1']
        gauge.tensor.velocity = np.array([10.0, 0.0, 0.0, 0.0], dtype=np.float32)
        gauge._prev_velocity_mag = 0.0
        for _ in range(50):
            engine.tick(1280, 720)
        assert not np.any(np.isnan(engine.tick(1280, 720)['rect']))


class TestHTMLSoundTriggerExtraction:
    """Verify the parser extracts sound-trigger attribute correctly."""

    def test_single_sound_trigger(self):
        from core.html_parser import AetherHTMLParser
        parser = AetherHTMLParser()
        html = '<aether-gauge id="g" value="50" sound-trigger="impact:0.8"></aether-gauge>'
        result = parser.parse(html)
        elem = result['elements'][0]
        assert elem['sound_trigger'] == 'impact:0.8'

    def test_multi_sound_trigger(self):
        from core.html_parser import AetherHTMLParser
        parser = AetherHTMLParser()
        html = '<aether-toggle id="t" sound-trigger="on:click_sound;off:release_sound"></aether-toggle>'
        result = parser.parse(html)
        elem = result['elements'][0]
        assert elem['sound_trigger'] == 'on:click_sound;off:release_sound'

    def test_settle_sound_trigger(self):
        from core.html_parser import AetherHTMLParser
        parser = AetherHTMLParser()
        html = '<aether-modal id="m" sound-trigger="settle"></aether-modal>'
        result = parser.parse(html)
        elem = result['elements'][0]
        assert elem['sound_trigger'] == 'settle'
