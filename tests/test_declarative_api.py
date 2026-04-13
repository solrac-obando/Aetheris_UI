# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Tests for the Declarative API (Flutter-like developer experience).
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPageCreation:
    """Test Page creation and configuration."""
    
    def test_page_creation(self):
        """Test Page can be created."""
        from core.declarative_api import Page
        
        page = Page(title="Test App", width=1280, height=720)
        
        assert page.title == "Test App"
        assert page.width == 1280
        assert page.height == 720
    
    def test_page_default_values(self):
        """Test Page default values."""
        from core.declarative_api import Page
        
        page = Page()
        
        assert page.title == "Aetheris App"
        assert page.width == 1280.0
        assert page.height == 720.0


class TestWidgetHierarchy:
    """Test widget creation and hierarchy."""
    
    def test_column_creation(self):
        """Test Column widget creation."""
        from core.declarative_api import Column, Text
        
        col = Column(controls=[Text("Hello")])
        
        assert col is not None
        assert len(col.controls) == 1
    
    def test_row_creation(self):
        """Test Row widget creation."""
        from core.declarative_api import Row, Container
        
        row = Row(controls=[Container(width=50), Container(width=50)])
        
        assert row is not None
        assert len(row.controls) == 2
    
    def test_container_creation(self):
        """Test Container widget creation."""
        from core.declarative_api import Container
        
        container = Container(width=100, height=50, padding=10)
        
        assert container._width == 100
        assert container._height == 50
        assert container._padding == 10
    
    def test_text_creation(self):
        """Test Text widget creation."""
        from core.declarative_api import Text
        
        text = Text("Hello World", size=20, color=(1, 0, 0, 1))
        
        assert text.value == "Hello World"
        assert text._size == 20
    
    def test_fluent_api(self):
        """Test fluent API for adding controls."""
        from core.declarative_api import Page, Column, Text, Row, Container
        
        page = Page()
        page.add(
            Column(controls=[
                Text("Title"),
                Row(controls=[
                    Container(width=50),
                    Container(width=50),
                ])
            ])
        )
        
        assert page._root is not None
        assert isinstance(page._root, Column)


class TestLayoutComputation:
    """Test layout mathematics."""
    
    def test_column_layout_simple(self):
        """Test simple column layout."""
        from core.declarative_api import Column, Text
        
        col = Column(controls=[
            Text("Item 1"),
            Text("Item 2"),
        ])
        
        col._compute_layout(0, 0, 1000, 1000)
        
        assert col._computed_x == 0
        assert col._computed_y == 0
        assert col._computed_w > 0
        assert col._computed_h > 0
    
    def test_row_layout_simple(self):
        """Test simple row layout."""
        from core.declarative_api import Row, Container
        
        row = Row(controls=[
            Container(width=100),
            Container(width=200),
        ])
        
        row._compute_layout(0, 0, 1000, 1000)
        
        assert row._computed_w > 0
        assert row._computed_h > 0
    
    def test_container_layout(self):
        """Test container with margin and padding."""
        from core.declarative_api import Container
        
        container = Container(
            width=200,
            height=100,
            margin=10,
            padding=5,
        )
        
        container._compute_layout(0, 0, 500, 500)
        
        assert container._computed_x == 10  # margin offset
        assert container._computed_y == 10
        assert container._computed_w == 220  # width + 2*margin
        assert container._computed_h == 120


class TestTextDimensions:
    """Test Text widget auto-sizing."""
    
    def test_text_dimensions_calculation(self):
        """Test text auto-sizes based on content and font size."""
        from core.declarative_api import Text
        
        text = Text("Hello", size=16)
        
        assert text._computed_w > 0
        assert text._computed_h > 0
        # Approximate: 5 chars * 16 * 0.6 = 48
        assert text._computed_w >= 40
    
    def test_text_empty(self):
        """Test empty text has zero dimensions."""
        from core.declarative_api import Text
        
        text = Text("")
        
        assert text._computed_w == 0
        assert text._computed_h == 0


class TestButton:
    """Test Button widget."""
    
    def test_button_creation(self):
        """Test Button creation."""
        from core.declarative_api import Button
        
        def on_click():
            pass
        
        btn = Button("Click Me", on_click=on_click)
        
        assert btn.text == "Click Me"
        assert btn.on_click is on_click
    
    def test_button_default_size(self):
        """Test button has default size."""
        from core.declarative_api import Button
        
        btn = Button("Test")
        
        btn._compute_layout(0, 0, 1000, 1000)
        
        assert btn._computed_w > 0
        assert btn._computed_h > 0


class TestStack:
    """Test Stack widget (absolute positioning)."""
    
    def test_stack_creation(self):
        """Test Stack creation."""
        from core.declarative_api import Stack, Container
        
        stack = Stack(controls=[
            Container(width=100, height=100),
            Container(width=50, height=50),
        ])
        
        assert stack is not None
        assert len(stack.controls) == 2
    
    def test_stack_layout(self):
        """Test stack computes max dimensions."""
        from core.declarative_api import Stack, Container
        
        stack = Stack(controls=[
            Container(width=100, height=100),
            Container(width=50, height=200),
        ])
        
        stack._compute_layout(0, 0, 500, 500)
        
        # Stack should be max of children
        assert stack._computed_w == 100
        assert stack._computed_h == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])