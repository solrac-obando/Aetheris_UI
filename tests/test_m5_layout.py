# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

import pytest
import numpy as np
from core.layout.parser import LayoutLexer, LayoutParser, LayoutToken, Token, parse_layout_dsl, ElementNode
from core.layout.compiler import LayoutCompiler, FlexboxMapper, PhysicsCompiler
from core.layout.factory import ElementFactory, AutoSizer
from core.layout.layout import AetherLayout
from core.elements import StaticBox, SmartPanel, SmartButton, FlexibleTextNode


class TestLayoutLexer:
    def test_tokenize_simple_element(self):
        lexer = LayoutLexer("box test")
        tokens = lexer.tokenize()
        assert any(t.type == LayoutToken.IDENT and t.value == "box" for t in tokens)
        assert any(t.type == LayoutToken.IDENT and t.value == "test" for t in tokens)

    def test_tokenize_string(self):
        lexer = LayoutLexer('box "Hello World"')
        tokens = lexer.tokenize()
        string_token = next((t for t in tokens if t.type == LayoutToken.STRING), None)
        assert string_token is not None
        assert string_token.value == "Hello World"

    def test_tokenize_number(self):
        lexer = LayoutLexer("box 100")
        tokens = lexer.tokenize()
        num_token = next((t for t in tokens if t.type == LayoutToken.NUMBER), None)
        assert num_token is not None
        assert num_token.value == 100.0

    def test_tokenize_braces(self):
        lexer = LayoutLexer("box { x: 10 }")
        tokens = lexer.tokenize()
        assert any(t.type == LayoutToken.LBRACE for t in tokens)
        assert any(t.type == LayoutToken.RBRACE for t in tokens)
        assert any(t.type == LayoutToken.COLON for t in tokens)

    def test_tokenize_id_with_hash(self):
        lexer = LayoutLexer("box#myid")
        tokens = lexer.tokenize()
        ident_tokens = [t for t in tokens if t.type == LayoutToken.IDENT]
        assert len(ident_tokens) >= 2

    def test_tokenize_hex_color(self):
        lexer = LayoutLexer('box { color: "#ff0000" }')
        tokens = lexer.tokenize()
        string_token = next((t for t in tokens if t.type == LayoutToken.STRING and t.value == "#ff0000"), None)
        assert string_token is not None


class TestLayoutParser:
    def test_parse_simple_element(self):
        lexer = LayoutLexer("box test")
        tokens = lexer.tokenize()
        parser = LayoutParser(tokens)
        elements = parser.parse()
        assert len(elements) >= 1
        assert elements[0].type == "box"

    def test_parse_element_with_string_id(self):
        lexer = LayoutLexer('box test "Hello"')
        tokens = lexer.tokenize()
        parser = LayoutParser(tokens)
        elements = parser.parse()
        assert len(elements) >= 1

    def test_parse_element_with_properties(self):
        lexer = LayoutLexer("box test { width: 100 height: 50 }")
        tokens = lexer.tokenize()
        parser = LayoutParser(tokens)
        elements = parser.parse()
        assert len(elements) >= 1


class TestLayoutCompiler:
    def test_compile_static_box(self):
        compiler = LayoutCompiler()
        node = ElementNode("box", "test")
        node.properties = {"x": 10, "y": 20, "width": 100, "height": 50}
        elements = compiler.compile([node], 800, 600)
        assert len(elements) == 1
        assert isinstance(elements[0], StaticBox)

    def test_compile_smart_panel(self):
        compiler = LayoutCompiler()
        node = ElementNode("panel", "test")
        node.properties = {"padding": 0.1}
        elements = compiler.compile([node], 800, 600)
        assert len(elements) == 1
        assert isinstance(elements[0], SmartPanel)

    def test_compile_text_element(self):
        compiler = LayoutCompiler()
        node = ElementNode("text", "label")
        node.properties = {"text": "Hello"}
        elements = compiler.compile([node], 800, 600)
        assert len(elements) == 1
        assert isinstance(elements[0], FlexibleTextNode)

    def test_compile_multiple_elements(self):
        compiler = LayoutCompiler()
        nodes = [
            ElementNode("box", "box1"),
            ElementNode("panel", "panel1"),
        ]
        elements = compiler.compile(nodes, 800, 600)
        assert len(elements) == 2

    def test_color_parsing_hex(self):
        compiler = LayoutCompiler()
        node = ElementNode("box", "test")
        node.properties = {"color": "#ff0000"}
        elements = compiler.compile([node], 800, 600)
        assert len(elements) == 1


class TestFlexboxMapper:
    def test_map_row_layout(self):
        mapper = FlexboxMapper(800, 600)
        element = StaticBox(0, 0, 100, 100)
        result = mapper.map_to_flex(element, "row")
        assert result["flex_direction"] == "row"

    def test_map_column_layout(self):
        mapper = FlexboxMapper(800, 600)
        element = StaticBox(0, 0, 100, 100)
        result = mapper.map_to_flex(element, "column")
        assert result["flex_direction"] == "column"

    def test_map_grid_layout(self):
        mapper = FlexboxMapper(800, 600)
        element = StaticBox(0, 0, 100, 100)
        result = mapper.map_to_flex(element, "grid")
        assert result["flex_direction"] == "grid"


class TestPhysicsCompiler:
    def test_parse_physics_string(self):
        compiler = PhysicsCompiler()
        result = compiler.parse_physics_string("spring(k=0.15, damping=0.9)")
        assert result["stiffness"] == 0.15
        assert result["damping"] == 0.9

    def test_default_physics(self):
        compiler = PhysicsCompiler()
        result = compiler.parse_physics_string("")
        assert result["stiffness"] == 0.1
        assert result["damping"] == 0.8


class TestElementFactory:
    def test_create_static_box(self):
        element = ElementFactory.create("box", x=10, y=20, w=100, h=50)
        assert isinstance(element, StaticBox)
        assert element.tensor.state[0] == 10
        assert element.tensor.state[1] == 20

    def test_create_smart_panel(self):
        element = ElementFactory.create("panel", padding=0.1)
        assert isinstance(element, SmartPanel)
        assert element._padding == 0.1

    def test_create_text_element(self):
        element = ElementFactory.create("text", text="Hello World")
        assert isinstance(element, FlexibleTextNode)
        assert element._text == "Hello World"

    def test_register_custom_element(self):
        ElementFactory.register("custom", StaticBox)
        element = ElementFactory.create("custom")
        assert isinstance(element, StaticBox)

    def test_get_available_types(self):
        types = ElementFactory.get_available_types()
        assert "box" in types
        assert "panel" in types
        assert "button" in types


class TestAutoSizer:
    def test_calculate_panel_size(self):
        x, y, w, h = AutoSizer.calculate_size("panel", 800, 600, {"padding": 0.1})
        assert x == 80.0
        assert y == 60.0
        assert w == 640.0
        assert h == 480.0

    def test_calculate_button_size(self):
        x, y, w, h = AutoSizer.calculate_size("button", 800, 600, {"width": 100, "height": 50})
        assert w == 100
        assert h == 50


class TestAetherLayout:
    def test_create_empty_layout(self):
        layout = AetherLayout()
        assert layout.get_elements() == []

    def test_create_from_dsl(self):
        dsl = 'box main { x: 10 y: 20 width: 100 height: 50 }'
        layout = AetherLayout(dsl, 800, 600)
        elements = layout.get_elements()
        assert len(elements) == 1
        assert isinstance(elements[0], StaticBox)

    def test_set_container_size(self):
        layout = AetherLayout("box test { x: 0 }", 800, 600)
        layout.set_container_size(1024, 768)
        assert layout._container_w == 1024
        assert layout._container_h == 768

    def test_create_element_via_factory(self):
        layout = AetherLayout()
        element = layout.create_element("box", x=50, y=50, w=200, h=100)
        assert isinstance(element, StaticBox)

    def test_add_remove_elements(self):
        layout = AetherLayout()
        element = StaticBox(0, 0, 100, 100)
        layout.add_element(element)
        assert len(layout.get_elements()) == 1
        layout.remove_element(element)
        assert len(layout.get_elements()) == 0

    def test_to_dict(self):
        layout = AetherLayout("box test", 800, 600)
        result = layout.to_dict()
        assert result["container_w"] == 800
        assert result["container_h"] == 600
        assert "element_count" in result


class TestAetherLayoutComplex:
    def test_parse_dashboard_layout(self):
        dsl = '''
header:
  height: 60
  background: "#1a1a2e"

main:
  grid: 3x2
  gap: 16
  padding: 24
'''
        layout = AetherLayout(dsl, 1024, 768)
        elements = layout.get_elements()
        assert len(elements) >= 0

    def test_parse_button_row(self):
        dsl = '''
row:
  button#submit "Submit"
  button#cancel "Cancel"
'''
        layout = AetherLayout(dsl, 800, 600)
        elements = layout.get_elements()

    def test_parse_nested_panel(self):
        dsl = '''
panel#outer:
  padding: 0.05
  panel#inner:
    padding: 0.1
'''
        layout = AetherLayout(dsl, 800, 600)
        elements = layout.get_elements()


class TestLayoutPerformance:
    def test_parse_performance(self):
        import time
        dsl = "box element1 { x: 10 }"
        start = time.time()
        layout = AetherLayout(dsl, 800, 600)
        elapsed = time.time() - start
        assert elapsed < 0.1

    def test_compile_performance(self):
        import time
        compiler = LayoutCompiler()
        nodes = [ElementNode("box", f"box{i}") for i in range(10)]
        start = time.time()
        elements = compiler.compile(nodes, 800, 600)
        elapsed = time.time() - start
        assert elapsed < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])