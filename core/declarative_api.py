# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Declarative API for Aetheris - Flutter-like Developer Experience.

This module provides a declarative, type-safe API that mimics Flutter/Flet's
widget tree pattern. Widgets like Column, Row, Container, and Text are
declarative descriptors that translate their layout math into native
Aetheris elements.

MATHEMATICAL LAYOUT LOGIC:
==========================

Column Layout:
  - Children are stacked vertically
  - Each child's Y = parent_y + sum(previous_heights) + spacing * index
  - X = parent_x (left-aligned by default)
  
Row Layout:
  - Children are arranged horizontally
  - Each child's X = parent_x + sum(previous_widths) + spacing * index
  - Y = parent_y (top-aligned by default)

Container:
  - Applies optional width/height constraints
  - Acts as a layout boundary with optional padding
  - Position = parent position + margin offset

Text:
  - Auto-sizes based on font_size and content length
  - Horizontal: font_size * len(content) * 0.6 (approx monospace width)
  - Vertical: font_size * 1.2
"""

from __future__ import annotations

import numpy as np
from typing import Any, Callable, Optional, Sequence, overload, Literal
from dataclasses import dataclass, field

from core.elements import DifferentialElement, SmartPanel, StaticBox, CanvasTextNode
from core.engine import AetherEngine


# Type aliases for better readability
ControlList = list["Widget"]
WidgetCallback = Callable[["Widget"], None]


class Widget:
    """
    Base class for all declarative widgets.
    
    Widgets are NOT rendered directly - they are mathematical descriptors
    that compute their layout and register native elements to the engine.
    """
    
    def __init__(
        self,
        controls: Optional[ControlList] = None,
        expand: bool = False,
        alignment: Optional[str] = None,
        padding: float = 0.0,
        margin: float = 0.0,
        width: Optional[float] = None,
        height: Optional[float] = None,
        bgcolor: Optional[tuple[float, float, float, float]] = None,
    ) -> None:
        self._controls: ControlList = controls or []
        self._expand = expand
        self._alignment = alignment
        self._padding = padding
        self._margin = margin
        self._width = width
        self._height = height
        self._bgcolor = bgcolor
        
        # Layout state (computed during layout pass)
        self._computed_x: float = 0.0
        self._computed_y: float = 0.0
        self._computed_w: float = 0.0
        self._computed_h: float = 0.0
        
        # Reference to native Aetheris element (created during build)
        self._native_element: Optional[DifferentialElement] = None
        self._parent: Optional[Widget] = None
        
        # Register as child of parent widgets
        for child in self._controls:
            child._parent = self
    
    @property
    def controls(self) -> ControlList:
        return self._controls
    
    @property
    def native_element(self) -> Optional[DifferentialElement]:
        return self._native_element
    
    def _compute_layout(
        self,
        parent_x: float,
        parent_y: float,
        available_w: float,
        available_h: float,
        spacing: float = 0.0,
    ) -> tuple[float, float]:
        """
        Compute absolute coordinates based on layout rules.
        
        Returns:
            Tuple of (total_width, total_height) consumed by this widget
        """
        return available_w, available_h
    
    def _build_native_element(self, engine: AetherEngine) -> None:
        """Build and register the native Aetheris element for this widget."""
        pass
    
    def add(self, widget: "Widget") -> "Widget":
        """Add a child widget (fluent API)."""
        self._controls.append(widget)
        widget._parent = self
        return self
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(controls={len(self._controls)})"


class Page:
    """
    The root container for a declarative Aetheris application.
    
    Acts as the bridge between the declarative widget tree and the native
    AetherEngine. All widgets are children of the Page.
    """
    
    def __init__(
        self,
        title: str = "Aetheris App",
        width: float = 1280.0,
        height: float = 720.0,
        theme: Optional[dict[str, Any]] = None,
    ) -> None:
        self._title = title
        self._width = width
        self._height = height
        self._theme = theme or {}
        
        # The root widget container
        self._root: Optional[Widget] = None
        
        # Reference to the native AetherEngine
        self._engine: Optional[AetherEngine] = None
        
        # Cached element counter for unique IDs
        self._element_counter = 0
    
    @property
    def title(self) -> str:
        return self._title
    
    @property
    def width(self) -> float:
        return self._width
    
    @property
    def height(self) -> float:
        return self._height
    
    @property
    def engine(self) -> Optional[AetherEngine]:
        return self._engine
    
    def _register_engine(self, engine: AetherEngine) -> None:
        """Internal: Register the AetherEngine instance."""
        self._engine = engine
    
    def add(self, widget: Widget) -> None:
        """Add a root-level widget to the page."""
        self._root = widget
    
    def _build(self) -> None:
        """Build the declarative widget tree into native elements."""
        if self._root is None or self._engine is None:
            return
        
        # Start layout computation from (0, 0) with full page available
        self._root._compute_layout(
            parent_x=0.0,
            parent_y=0.0,
            available_w=self._width,
            available_h=self._height,
        )
        
        # Build all native elements
        self._root._build_native_element(self._engine)
    
    def _next_id(self) -> str:
        """Generate unique element ID."""
        self._element_counter += 1
        return f"aetheris_{self._element_counter}"
    
    def __repr__(self) -> str:
        return f"Page(title='{self._title}', size={self._width}x{self._height})"


class Container(Widget):
    """
    A flexible container that can hold other widgets.
    
    MATH:
      - Applies margin as offset from parent position
      - Applies padding as internal offset for children
      - Width/Height constrain the content area
    """
    
    _id_counter = 0
    
    def __init__(
        self,
        controls: Optional[ControlList] = None,
        width: Optional[float] = None,
        height: Optional[float] = None,
        padding: float = 0.0,
        margin: float = 0.0,
        bgcolor: Optional[tuple[float, float, float, float]] = None,
        border_width: float = 0.0,
        border_color: Optional[tuple[float, float, float, float]] = None,
        alignment: Optional[Literal["center", "left", "right", "top", "bottom"]] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            controls=controls,
            width=width,
            height=height,
            padding=padding,
            margin=margin,
            bgcolor=bgcolor,
            **kwargs,
        )
        self._border_width = border_width
        self._border_color = border_color
        self._alignment = alignment
        Container._id_counter += 1
        self._id = Container._id_counter
    
    def _compute_layout(
        self,
        parent_x: float,
        parent_y: float,
        available_w: float,
        available_h: float,
        spacing: float = 0.0,
    ) -> tuple[float, float]:
        # Apply margin offset
        self._computed_x = parent_x + self._margin
        self._computed_y = parent_y + self._margin
        
        # Determine dimensions
        content_w = self._width if self._width is not None else available_w
        content_h = self._height if self._height is not None else available_h
        
        self._computed_w = content_w + 2 * self._margin
        self._computed_h = content_h + 2 * self._margin
        
        # Compute children layout with padding offset
        inner_x = self._computed_x + self._padding
        inner_y = self._computed_y + self._padding
        inner_w = content_w - 2 * self._padding
        inner_h = content_h - 2 * self._padding
        
        for child in self._controls:
            child._compute_layout(inner_x, inner_y, inner_w, inner_h, spacing)
        
        return self._computed_w, self._computed_h
    
    def _build_native_element(self, engine: AetherEngine) -> None:
        """Build StaticBox as native element."""
        element_id = f"container_{self._id}"
        
        self._native_element = StaticBox(
            x=self._computed_x,
            y=self._computed_y,
            w=self._computed_w,
            h=self._computed_h,
            color=self._bgcolor or (0.2, 0.2, 0.2, 1.0),
            z=0,
        )
        
        engine.register(self._native_element)
        
        # Build children
        for child in self._controls:
            child._build_native_element(engine)


class Column(Widget):
    """
    A vertical column of widgets.
    
    MATH:
      - Y coordinate: parent_y + sum(previous_heights) + spacing * index
      - X coordinate: parent_x + alignment_offset (center/left/right)
      - Width: max(child_widths) or available_width if expand
      - Height: sum(child_heights) + spacing * (n-1)
    """
    
    def __init__(
        self,
        controls: Optional[ControlList] = None,
        spacing: float = 0.0,
        alignment: Optional[Literal["start", "center", "end"]] = "start",
        expand: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(controls=controls, expand=expand, **kwargs)
        self._spacing = spacing
        self._alignment = alignment
    
    def _compute_layout(
        self,
        parent_x: float,
        parent_y: float,
        available_w: float,
        available_h: float,
        spacing: float = 0.0,
    ) -> tuple[float, float]:
        effective_spacing = spacing + self._spacing
        
        # Calculate each child's position
        current_y = parent_y
        
        max_child_width = 0.0
        total_height = 0.0
        
        for i, child in enumerate(self._controls):
            # Compute child's layout
            child_w, child_h = child._compute_layout(
                parent_x=parent_x,
                parent_y=current_y,
                available_w=available_w,
                available_h=available_h - current_y + parent_y,
                spacing=effective_spacing,
            )
            
            # Apply horizontal alignment
            if self._alignment == "center":
                align_offset = (available_w - child_w) / 2
            elif self._alignment == "end":
                align_offset = available_w - child_w
            else:  # start
                align_offset = 0.0
            
            child._computed_x = parent_x + align_offset
            
            max_child_width = max(max_child_width, child_w)
            total_height += child_h
            
            # Move to next row
            current_y += child_h + effective_spacing
        
        self._computed_x = parent_x
        self._computed_y = parent_y
        self._computed_w = max_child_width if not self._expand else available_w
        self._computed_h = max(0, total_height - effective_spacing)  # Remove last spacing
        
        return self._computed_w, self._computed_h
    
    def _build_native_element(self, engine: AetherEngine) -> None:
        """Column itself doesn't create an element; it orchestrates children."""
        for child in self._controls:
            child._build_native_element(engine)


class Row(Widget):
    """
    A horizontal row of widgets.
    
    MATH:
      - X coordinate: parent_x + sum(previous_widths) + spacing * index
      - Y coordinate: parent_y + alignment_offset (top/center/bottom)
      - Height: max(child_heights) or available_height if expand
      - Width: sum(child_widths) + spacing * (n-1)
    """
    
    def __init__(
        self,
        controls: Optional[ControlList] = None,
        spacing: float = 0.0,
        alignment: Optional[Literal["start", "center", "end"]] = "start",
        expand: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(controls=controls, expand=expand, **kwargs)
        self._spacing = spacing
        self._alignment = alignment
    
    def _compute_layout(
        self,
        parent_x: float,
        parent_y: float,
        available_w: float,
        available_h: float,
        spacing: float = 0.0,
    ) -> tuple[float, float]:
        effective_spacing = spacing + self._spacing
        
        # Calculate each child's position
        current_x = parent_x
        
        max_child_height = 0.0
        total_width = 0.0
        
        for i, child in enumerate(self._controls):
            # Compute child's layout
            child_w, child_h = child._compute_layout(
                parent_x=current_x,
                parent_y=parent_y,
                available_w=available_w - current_x + parent_x,
                available_h=available_h,
                spacing=effective_spacing,
            )
            
            # Apply vertical alignment
            if self._alignment == "center":
                align_offset = (available_h - child_h) / 2
            elif self._alignment == "end":
                align_offset = available_h - child_h
            else:  # start
                align_offset = 0.0
            
            child._computed_y = parent_y + align_offset
            
            max_child_height = max(max_child_height, child_h)
            total_width += child_w
            
            # Move to next column
            current_x += child_w + effective_spacing
        
        self._computed_x = parent_x
        self._computed_y = parent_y
        self._computed_w = max(0, total_width - effective_spacing)  # Remove last spacing
        self._computed_h = max_child_height if not self._expand else available_h
        
        return self._computed_w, self._computed_h
    
    def _build_native_element(self, engine: AetherEngine) -> None:
        """Row itself doesn't create an element; it orchestrates children."""
        for child in self._controls:
            child._build_native_element(engine)


class Text(Widget):
    """
    A text widget that renders text content.
    
    MATH:
      - Width ≈ len(text) * font_size * 0.6 (monospace approximation)
      - Height ≈ font_size * 1.2 (line height)
      - Position: based on parent layout
    """
    
    _id_counter = 0
    
    def __init__(
        self,
        value: str = "",
        size: float = 16.0,
        color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
        font_family: str = "monospace",
        weight: Optional[Literal["normal", "bold"]] = "normal",
        align: Optional[Literal["left", "center", "right"]] = "left",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._value = value
        self._size = size
        self._color = color
        self._font_family = font_family
        self._weight = weight
        self._align = align
        
        Text._id_counter += 1
        self._id = Text._id_counter
        
        # Auto-compute dimensions based on content
        self._computed_w = len(value) * size * 0.6 if value else 0
        self._computed_h = size * 1.2 if value else 0  # 0 height for empty text
    
    @property
    def value(self) -> str:
        return self._value
    
    def _compute_layout(
        self,
        parent_x: float,
        parent_y: float,
        available_w: float,
        available_h: float,
        spacing: float = 0.0,
    ) -> tuple[float, float]:
        self._computed_x = parent_x
        self._computed_y = parent_y
        
        # Recalculate dimensions based on available width
        if self._width:
            self._computed_w = self._width
        else:
            self._computed_w = min(len(self._value) * self._size * 0.6, available_w)
        
        self._computed_h = self._height if self._height else self._size * 1.2
        
        return self._computed_w, self._computed_h
    
    def _build_native_element(self, engine: AetherEngine) -> None:
        """Build CanvasTextNode as native element."""
        element_id = f"text_{self._id}"
        
        self._native_element = CanvasTextNode(
            x=self._computed_x,
            y=self._computed_y,
            w=self._computed_w,
            h=self._computed_h,
            text=self._value,
            font_size=self._size,
            color=self._color,
        )
        
        engine.register(self._native_element)


class Stack(Widget):
    """
    A widget that positions children absolutely (overlapping).
    
    MATH:
      - All children start at parent's origin (0, 0 offset)
      - Position is determined by each child's explicit x/y
      - Size is max of all children's sizes
    """
    
    def __init__(
        self,
        controls: Optional[ControlList] = None,
        **kwargs,
    ) -> None:
        super().__init__(controls=controls, **kwargs)
    
    def _compute_layout(
        self,
        parent_x: float,
        parent_y: float,
        available_w: float,
        available_h: float,
        spacing: float = 0.0,
    ) -> tuple[float, float]:
        max_w, max_h = 0.0, 0.0
        
        for child in self._controls:
            child._compute_layout(parent_x, parent_y, available_w, available_h, 0)
            max_w = max(max_w, child._computed_w)
            max_h = max(max_h, child._computed_h)
        
        self._computed_x = parent_x
        self._computed_y = parent_y
        self._computed_w = max_w
        self._computed_h = max_h
        
        return self._computed_w, self._computed_h
    
    def _build_native_element(self, engine: AetherEngine) -> None:
        for child in self._controls:
            child._build_native_element(engine)


class Image(Widget):
    """
    An image widget for displaying images.
    
    MATH:
      - Dimensions based on width/height or aspect ratio
      - Position from parent layout
    """
    
    _id_counter = 0
    
    def __init__(
        self,
        src: str = "",
        width: Optional[float] = None,
        height: Optional[float] = None,
        fit: Optional[Literal["contain", "cover", "fill"]] = "contain",
        **kwargs,
    ) -> None:
        super().__init__(width=width, height=height, **kwargs)
        self._src = src
        self._fit = fit
        Image._id_counter += 1
        self._id = Image._id_counter
    
    def _compute_layout(
        self,
        parent_x: float,
        parent_y: float,
        available_w: float,
        available_h: float,
        spacing: float = 0.0,
    ) -> tuple[float, float]:
        self._computed_x = parent_x
        self._computed_y = parent_y
        self._computed_w = self._width if self._width else available_w
        self._computed_h = self._height if self._height else available_h
        return self._computed_w, self._computed_h
    
    def _build_native_element(self, engine: AetherEngine) -> None:
        element_id = f"image_{self._id}"
        
        self._native_element = StaticBox(
            x=self._computed_x,
            y=self._computed_y,
            w=self._computed_w,
            h=self._computed_h,
            color=(0.3, 0.3, 0.3, 1.0),  # Placeholder color
            z=0,
        )
        
        engine.register(self._native_element)


class Button(Widget):
    """
    A button widget with text and optional icon.
    
    MATH:
      - Auto-sizes based on text content + padding
      - Position from parent layout
    """
    
    _id_counter = 0
    
    def __init__(
        self,
        text: str = "",
        on_click: Optional[Callable[[], None]] = None,
        width: Optional[float] = None,
        height: Optional[float] = None,
        bgcolor: tuple[float, float, float, float] = (0.2, 0.5, 0.8, 1.0),
        **kwargs,
    ) -> None:
        super().__init__(width=width, height=height, bgcolor=bgcolor, **kwargs)
        self._text = text
        self._on_click = on_click
        Button._id_counter += 1
        self._id = Button._id_counter
    
    @property
    def text(self) -> str:
        return self._text
    
    @property
    def on_click(self) -> Optional[Callable[[], None]]:
        return self._on_click
    
    def _compute_layout(
        self,
        parent_x: float,
        parent_y: float,
        available_w: float,
        available_h: float,
        spacing: float = 0.0,
    ) -> tuple[float, float]:
        self._computed_x = parent_x
        self._computed_y = parent_y
        
        if self._width:
            self._computed_w = self._width
        else:
            self._computed_w = len(self._text) * 10.0 + 20.0  # Text + padding
        
        if self._height:
            self._computed_h = self._height
        else:
            self._computed_h = 40.0  # Default button height
        
        return self._computed_w, self._computed_h
    
    def _build_native_element(self, engine: AetherEngine) -> None:
        element_id = f"button_{self._id}"
        
        self._native_element = SmartPanel(
            x=self._computed_x,
            y=self._computed_y,
            w=self._computed_w,
            h=self._computed_h,
            color=self._bgcolor or (0.2, 0.5, 0.8, 1.0),
            z=0,
        )
        
        engine.register(self._native_element)


# Export all widget classes
__all__ = [
    "Widget",
    "Page",
    "Container",
    "Column",
    "Row",
    "Stack",
    "Text",
    "Image",
    "Button",
    "ControlList",
]