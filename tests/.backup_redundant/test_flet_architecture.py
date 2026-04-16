# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Specific tests for Flet-like declarative API.

These tests verify the Flutter/Flet-like developer experience:
- Widget tree construction
- Layout computation mathematics
- Native element generation
- Fluent API patterns
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestFletLikePage:
    """Test Page class as root of declarative API."""
    
    def test_page_with_title(self):
        """Test Page accepts title parameter."""
        from core.declarative_api import Page
        
        page = Page(title="My Dashboard")
        
        assert page.title == "My Dashboard"
    
    def test_page_with_custom_size(self):
        """Test Page accepts custom dimensions."""
        from core.declarative_api import Page
        
        page = Page(width=1920, height=1080)
        
        assert page.width == 1920
        assert page.height == 1080
    
    def test_page_add_widget(self):
        """Test Page.add() accepts widget."""
        from core.declarative_api import Page, Column
        
        page = Page()
        column = Column()
        
        page.add(column)
        
        assert page._root is column
    
    def test_page_generates_unique_ids(self):
        """Test Page generates unique element IDs."""
        from core.declarative_api import Page, Text
        
        page = Page()
        
        id1 = page._next_id()
        id2 = page._next_id()
        
        assert id1 != id2
        assert id1.startswith("aetheris_")


class TestFletLikeColumn:
    """Test Column widget vertical layout."""
    
    def test_column_default_alignment(self):
        """Test Column default alignment is start (left)."""
        from core.declarative_api import Column
        
        col = Column()
        
        assert col._alignment == "start"
    
    def test_column_center_alignment(self):
        """Test Column center alignment."""
        from core.declarative_api import Column
        
        col = Column(alignment="center")
        
        assert col._alignment == "center"
    
    def test_column_end_alignment(self):
        """Test Column end alignment."""
        from core.declarative_api import Column
        
        col = Column(alignment="end")
        
        assert col._alignment == "end"
    
    def test_column_spacing(self):
        """Test Column spacing parameter."""
        from core.declarative_api import Column
        
        col = Column(spacing=10.0)
        
        assert col._spacing == 10.0
    
    def test_column_expand_flag(self):
        """Test Column expand flag."""
        from core.declarative_api import Column
        
        col = Column(expand=True)
        
        assert col._expand is True
    
    def test_column_vertical_layout_math(self):
        """Test Column computes vertical layout correctly."""
        from core.declarative_api import Column, Container
        
        col = Column(controls=[
            Container(height=50),
            Container(height=30),
            Container(height=20),
        ], spacing=5)
        
        col._compute_layout(0, 0, 1000, 1000)
        
        # Y positions: 0, 55 (50+5), 90 (55+30+5)
        assert col._controls[0]._computed_y == 0
        assert col._controls[1]._computed_y == 55
        assert col._controls[2]._computed_y == 90
        
        # Total height: 50 + 30 + 20 = 100 (last spacing subtracted)
        assert col._computed_h == 95
    
    def test_column_center_alignment_shifts_children(self):
        """Test center alignment shifts children horizontally."""
        from core.declarative_api import Column, Container
        
        col = Column(controls=[
            Container(width=100),
        ], alignment="center")
        
        col._compute_layout(0, 0, 500, 1000)
        
        # Center of 500 is 250, child width is 100, offset = (500-100)/2 = 200
        assert col._controls[0]._computed_x == 200


class TestFletLikeRow:
    """Test Row widget horizontal layout."""
    
    def test_row_default_alignment(self):
        """Test Row default alignment is start (top)."""
        from core.declarative_api import Row
        
        row = Row()
        
        assert row._alignment == "start"
    
    def test_row_spacing(self):
        """Test Row spacing parameter."""
        from core.declarative_api import Row
        
        row = Row(spacing=15.0)
        
        assert row._spacing == 15.0
    
    def test_row_horizontal_layout_math(self):
        """Test Row computes horizontal layout correctly."""
        from core.declarative_api import Row, Container
        
        row = Row(controls=[
            Container(width=50),
            Container(width=30),
            Container(width=20),
        ], spacing=5)
        
        row._compute_layout(0, 0, 1000, 1000)
        
        # X positions: 0, 55 (50+5), 90 (55+30+5)
        assert row._controls[0]._computed_x == 0
        assert row._controls[1]._computed_x == 55
        assert row._controls[2]._computed_x == 90
        
        # Total width: 50 + 30 + 20 = 100 (last spacing subtracted)
        assert row._computed_w == 95
    
    def test_row_vertical_center_alignment(self):
        """Test center alignment shifts children vertically."""
        from core.declarative_api import Row, Container
        
        row = Row(controls=[
            Container(height=50),
        ], alignment="center")
        
        row._compute_layout(0, 0, 1000, 200)
        
        # Center of 200 is 100, child height is 50, offset = (200-50)/2 = 75
        assert row._controls[0]._computed_y == 75


class TestFletLikeContainer:
    """Test Container widget with margin/padding/border."""
    
    def test_container_margin_offset(self):
        """Test container margin offsets position."""
        from core.declarative_api import Container
        
        container = Container(margin=10, width=100, height=50)
        
        container._compute_layout(0, 0, 500, 500)
        
        assert container._computed_x == 10
        assert container._computed_y == 10
    
    def test_container_padding_affects_children(self):
        """Test container padding offsets children."""
        from core.declarative_api import Container, Text
        
        container = Container(
            width=200,
            height=100,
            padding=20,
            margin=0,
        )
        container.add(Text("Hello"))
        
        container._compute_layout(0, 0, 500, 500)
        
        # Children start at 0+20 = 20
        assert container._controls[0]._computed_x == 20
        assert container._controls[0]._computed_y == 20
    
    def test_container_border_width(self):
        """Test container border width parameter."""
        from core.declarative_api import Container
        
        container = Container(border_width=2)
        
        assert container._border_width == 2
    
    def test_container_bgcolor(self):
        """Test container background color."""
        from core.declarative_api import Container
        
        container = Container(bgcolor=(1, 0, 0, 1))
        
        assert container._bgcolor == (1, 0, 0, 1)


class TestFletLikeText:
    """Test Text widget auto-sizing."""
    
    def test_text_dimension_calculation(self):
        """Test text auto-calculates dimensions."""
        from core.declarative_api import Text
        
        text = Text("Hello", size=20)
        
        # Expected: 5 chars * 20 * 0.6 = 60 width, 20 * 1.2 = 24 height
        assert text._computed_w >= 50
        assert text._computed_h >= 20
    
    def test_text_custom_color(self):
        """Test text accepts custom color."""
        from core.declarative_api import Text
        
        text = Text("Test", color=(1, 0, 0, 1))
        
        assert text._color == (1, 0, 0, 1)
    
    def test_text_font_family(self):
        """Test text accepts font family."""
        from core.declarative_api import Text
        
        text = Text("Test", font_family="Arial")
        
        assert text._font_family == "Arial"
    
    def test_text_weight(self):
        """Test text weight parameter."""
        from core.declarative_api import Text
        
        text = Text("Test", weight="bold")
        
        assert text._weight == "bold"


class TestFletLikeStack:
    """Test Stack widget for absolute positioning."""
    
    def test_stack_overlapping_children(self):
        """Test stack positions children at same origin."""
        from core.declarative_api import Stack, Container
        
        stack = Stack(controls=[
            Container(width=100, height=100),
            Container(width=50, height=50),
        ])
        
        stack._compute_layout(0, 0, 500, 500)
        
        # Both children start at same position (0, 0)
        assert stack._controls[0]._computed_x == 0
        assert stack._controls[0]._computed_y == 0
        assert stack._controls[1]._computed_x == 0
        assert stack._controls[1]._computed_y == 0
    
    def test_stack_max_dimensions(self):
        """Test stack takes max of children dimensions."""
        from core.declarative_api import Stack, Container
        
        stack = Stack(controls=[
            Container(width=100, height=100),
            Container(width=50, height=200),
        ])
        
        stack._compute_layout(0, 0, 500, 500)
        
        assert stack._computed_w == 100
        assert stack._computed_h == 200


class TestFletLikeButton:
    """Test Button widget."""
    
    def test_button_text(self):
        """Test button stores text."""
        from core.declarative_api import Button as Btn
        
        button = Btn("Click Me")
        
        assert button.text == "Click Me"
    
    def test_button_callback(self):
        """Test button stores callback."""
        from core.declarative_api import Button as Btn
        
        def on_click():
            pass
        
        button = Btn("Click", on_click=on_click)
        
        assert button.on_click is on_click
    
    def test_button_default_size(self):
        """Test button has default size calculation."""
        from core.declarative_api import Button as Btn
        
        button = Btn("Test Button")
        
        button._compute_layout(0, 0, 1000, 1000)
        
        assert button._computed_w > 0
        assert button._computed_h > 0


class TestFletLikeFluentAPI:
    """Test fluent API pattern for widget construction."""
    
    def test_add_returns_self(self):
        """Test add() returns self for chaining."""
        from core.declarative_api import Container, Text
        
        container = Container()
        result = container.add(Text("Hello"))
        
        assert result is container
    
    def test_nested_fluent_pattern(self):
        """Test fluent pattern with nested widgets."""
        from core.declarative_api import Page, Column, Row, Container, Text
        
        page = Page()
        page.add(
            Column().add(
                Text("Title", size=24)
            ).add(
                Row().add(
                    Container(width=50).add(
                        Text("A")
                    )
                ).add(
                    Container(width=50).add(
                        Text("B")
                    )
                )
            )
        )
        
        assert page._root is not None
        assert isinstance(page._root, Column)
    
    def test_controls_property(self):
        """Test controls property returns list."""
        from core.declarative_api import Column, Text, Container
        
        col = Column(controls=[
            Text("A"),
            Container(width=100),
        ])
        
        assert len(col.controls) == 2
        assert isinstance(col.controls, list)


class TestNativeElementGeneration:
    """Test widgets generate native Aetheris elements."""
    
    def test_text_generates_canvas_text_node(self):
        """Test Text generates CanvasTextNode."""
        from core.declarative_api import Page, Text
        from core.engine import AetherEngine
        from core.elements import CanvasTextNode
        
        page = Page()
        engine = AetherEngine()
        page._register_engine(engine)
        
        page.add(Text("Hello"))
        page._build()
        
        assert engine.element_count == 1
        element = engine.get_all_elements()[0]
        assert isinstance(element, CanvasTextNode)
    
    def test_container_generates_static_box(self):
        """Test Container generates StaticBox."""
        from core.declarative_api import Page, Container
        from core.engine import AetherEngine
        from core.elements import StaticBox
        
        page = Page()
        engine = AetherEngine()
        page._register_engine(engine)
        
        page.add(Container(width=100, height=50))
        page._build()
        
        element = engine.get_all_elements()[0]
        assert isinstance(element, StaticBox)
    
    def test_button_generates_smart_panel(self):
        """Test Button generates SmartPanel."""
        from core.declarative_api import Page, Button
        from core.engine import AetherEngine
        from core.elements import SmartPanel
        
        page = Page()
        engine = AetherEngine()
        page._register_engine(engine)
        
        page.add(Button("Click"))
        page._build()
        
        element = engine.get_all_elements()[0]
        assert isinstance(element, SmartPanel)


class TestLayoutEdgeCases:
    """Test edge cases in layout computation."""
    
    def test_empty_column(self):
        """Test empty column has zero height."""
        from core.declarative_api import Column
        
        col = Column()
        
        col._compute_layout(0, 0, 100, 100)
        
        assert col._computed_h == 0
    
    def test_empty_row(self):
        """Test empty row has zero width."""
        from core.declarative_api import Row
        
        row = Row()
        
        row._compute_layout(0, 0, 100, 100)
        
        assert row._computed_w == 0
    
    def test_container_with_no_children(self):
        """Test container with no children but explicit size."""
        from core.declarative_api import Container
        
        container = Container(width=100, height=50)
        
        container._compute_layout(0, 0, 500, 500)
        
        assert container._computed_w == 100
        assert container._computed_h == 50
    
    def test_nested_layout_depth(self):
        """Test deeply nested layout."""
        from core.declarative_api import Column, Row, Container
        
        nested = Column(controls=[
            Row(controls=[
                Column(controls=[
                    Container(width=10, height=10)
                ])
            ])
        ])
        
        nested._compute_layout(0, 0, 1000, 1000)
        
        # Should complete without error
        assert nested._computed_w > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])