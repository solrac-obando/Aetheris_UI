# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Unit tests for core/html_parser.py - AetherHTMLParser.

Verifies tag-to-element mapping, CSS parsing, color normalization,
spring transition detection, and JSON intent output.
"""
import pytest
from core.html_parser import AetherHTMLParser


class TestAetherHTMLParser:

    def setup_method(self):
        self.parser = AetherHTMLParser()

    def test_basic_div_maps_to_static_box(self):
        html = '<div id="main">Content</div>'
        result = self.parser.parse(html)
        assert len(result['elements']) == 1
        assert result['elements'][0]['type'] == 'static_box'
        assert result['elements'][0]['id'] == 'main'

    def test_button_maps_to_smart_button(self):
        html = '<button id="submit">Click Me</button>'
        result = self.parser.parse(html)
        assert result['elements'][0]['type'] == 'smart_button'
        assert result['elements'][0]['id'] == 'submit'

    def test_heading_maps_to_canvas_text(self):
        html = '<h1 id="title">Hello</h1>'
        result = self.parser.parse(html)
        assert result['elements'][0]['type'] == 'canvas_text'
        assert result['elements'][0]['text_content'] == 'Hello'

    def test_paragraph_maps_to_flexible_text(self):
        html = '<p id="desc">Description</p>'
        result = self.parser.parse(html)
        assert result['elements'][0]['type'] == 'flexible_text'
        assert result['elements'][0]['text_content'] == 'Description'

    def test_label_maps_to_dom_text(self):
        html = '<label id="lbl">Name</label>'
        result = self.parser.parse(html)
        assert result['elements'][0]['type'] == 'dom_text'

    def test_nested_elements(self):
        html = '''
        <div id="panel">
            <button id="btn">Click</button>
        </div>
        '''
        result = self.parser.parse(html)
        assert len(result['elements']) == 2
        ids = [e['id'] for e in result['elements']]
        assert 'panel' in ids
        assert 'btn' in ids

    def test_css_background_color_hex(self):
        html = '<div id="box"></div>'
        css = '#box { background-color: #ff0000; }'
        result = self.parser.parse(html, css)
        elem = result['elements'][0]
        assert 'color' in elem
        assert elem['color'][0] == pytest.approx(1.0)
        assert elem['color'][1] == pytest.approx(0.0)
        assert elem['color'][2] == pytest.approx(0.0)
        assert elem['color'][3] == pytest.approx(1.0)

    def test_css_background_color_rgba(self):
        html = '<div id="box"></div>'
        css = '#box { background-color: rgba(128, 128, 128, 0.5); }'
        result = self.parser.parse(html, css)
        elem = result['elements'][0]
        assert elem['color'][0] == pytest.approx(0.502, abs=0.01)
        assert elem['color'][3] == pytest.approx(0.5)

    def test_css_background_color_8digit_hex(self):
        html = '<div id="box"></div>'
        css = '#box { background-color: #e63399cc; }'
        result = self.parser.parse(html, css)
        elem = result['elements'][0]
        assert elem['color'][0] == pytest.approx(0.902, abs=0.01)
        assert elem['color'][1] == pytest.approx(0.2, abs=0.01)
        assert elem['color'][2] == pytest.approx(0.6, abs=0.01)
        assert elem['color'][3] == pytest.approx(0.8, abs=0.01)

    def test_spring_transition_parsing(self):
        html = '<div id="card"></div>'
        css = '#card { transition: transform 0.3s aether-spring(k=20, c=1.5); }'
        result = self.parser.parse(html, css)
        assert len(result.get('transitions', [])) == 1
        t = result['transitions'][0]
        assert t['easing'] == 'aether_spring'
        assert t['spring_k'] == 20.0
        assert t['spring_c'] == 1.5
        assert t['duration'] == 0.3

    def test_spring_function_alias(self):
        html = '<div id="card"></div>'
        css = '#card { transition: all 0.5s spring(k=15.0, c=2.5); }'
        result = self.parser.parse(html, css)
        t = result['transitions'][0]
        assert t['easing'] == 'aether_spring'
        assert t['spring_k'] == 15.0
        assert t['spring_c'] == 2.5

    def test_class_selector_matching(self):
        html = '<div class="main-panel"></div>'
        css = '.main-panel { background-color: #00ff00; }'
        result = self.parser.parse(html, css)
        elem = result['elements'][0]
        assert elem['color'][1] == pytest.approx(1.0)

    def test_id_selector_takes_precedence_over_class(self):
        html = '<div id="special" class="main-panel"></div>'
        css = '''
        .main-panel { background-color: #00ff00; }
        #special { background-color: #ff0000; }
        '''
        result = self.parser.parse(html, css)
        elem = result['elements'][0]
        assert elem['color'][0] == pytest.approx(1.0)
        assert elem['color'][1] == pytest.approx(0.0)

    def test_percentage_dimensions(self):
        html = '<div id="box"></div>'
        css = '#box { width: 50%; height: 25%; }'
        result = self.parser.parse(html, css)
        elem = result['elements'][0]
        assert elem['w'] == 400.0
        assert elem['h'] == 150.0

    def test_pixel_dimensions(self):
        html = '<div id="box"></div>'
        css = '#box { width: 300px; height: 200px; }'
        result = self.parser.parse(html, css)
        elem = result['elements'][0]
        assert elem['w'] == 300.0
        assert elem['h'] == 200.0

    def test_font_size_from_css(self):
        html = '<h1 id="title">Big</h1>'
        css = '#title { font-size: 48px; }'
        result = self.parser.parse(html, css)
        elem = result['elements'][0]
        assert elem['font_size'] == 48

    def test_empty_css(self):
        html = '<div id="box"></div>'
        result = self.parser.parse(html, '')
        assert len(result['elements']) == 1
        assert result['elements'][0]['id'] == 'box'

    def test_no_animation_key_if_no_transitions(self):
        html = '<div id="box"></div>'
        result = self.parser.parse(html)
        assert result.get('transitions', []) == []

    def test_unknown_tag_defaults_to_static_box(self):
        html = '<custom-element id="weird"></custom-element>'
        result = self.parser.parse(html)
        assert result['elements'][0]['type'] == 'static_box'

    def test_parent_reference_for_nested_buttons(self):
        html = '''
        <div id="panel">
            <button id="btn">Go</button>
        </div>
        '''
        result = self.parser.parse(html)
        btn = [e for e in result['elements'] if e['id'] == 'btn'][0]
        assert btn.get('parent') == 'panel'

    def test_text_extraction(self):
        html = '<p id="para">Hello World</p>'
        result = self.parser.parse(html)
        assert result['elements'][0]['text_content'] == 'Hello World'

    def test_transform_parsing(self):
        html = '<div id="card"></div>'
        css = '#card:hover { transform: scale(1.1); }'
        result = self.parser.parse(html, css)
        assert len(result['elements']) == 1

    def test_multiple_elements_same_class(self):
        html = '''
        <div class="card">First</div>
        <div class="card">Second</div>
        '''
        css = '.card { background-color: #333333; }'
        result = self.parser.parse(html, css)
        assert len(result['elements']) == 2
        for elem in result['elements']:
            assert elem['color'][0] == pytest.approx(0.2, abs=0.01)

    def test_rem_font_size(self):
        html = '<p id="text">Rem sized</p>'
        css = '#text { font-size: 1.5rem; }'
        result = self.parser.parse(html, css)
        assert result['elements'][0]['font_size'] == 24

    def test_ms_duration(self):
        html = '<div id="box"></div>'
        css = '#box { transition: opacity 500ms ease; }'
        result = self.parser.parse(html, css)
        t = result['transitions'][0]
        assert t['duration'] == 0.5
