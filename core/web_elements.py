# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Aether-Web Elements: HTML-native UI elements with physics.

These elements inherit from DifferentialElement but carry additional
metadata for HTML rendering (tag, classes, text content, input type).
They bridge the gap between physics-driven positioning and native
HTML/CSS rendering in the browser.
"""
import numpy as np
from typing import Dict, Any, Optional, List
from core.elements import DifferentialElement


class WebElement(DifferentialElement):
    """
    Base class for web-renderable physics elements.

    Carries HTML metadata (tag, classes, text) alongside physics state.
    """

    def __init__(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        color=(0.3, 0.3, 0.3, 0.9),
        z: int = 0,
        html_tag: str = "div",
        css_classes: Optional[List[str]] = None,
        styles: Optional[Dict[str, str]] = None,
        html_id: Optional[str] = None,
    ):
        super().__init__(x, y, w, h, color=color, z=z)
        self._html_tag = html_tag
        self._css_classes = css_classes or []
        self._styles = styles or {}
        self._html_id = html_id or f"ae_{id(self)}_{z}"
        self._target = np.array([x, y, w, h], dtype=np.float32)

    def calculate_asymptotes(self, container_w: float, container_h: float) -> np.ndarray:
        return self._target.copy()

    @property
    def html_metadata(self) -> Dict[str, Any]:
        """Return metadata for HTML rendering."""
        return {
            "tag": self._html_tag,
            "classes": self._css_classes,
            "styles": self._styles,
            "id": self._html_id,
        }


class WebButton(WebElement):
    """
    Interactive HTML button with physics properties.

    Renders as a <button> element in the browser. Supports click events
    that propagate back to the Python engine via the WebSocket bridge.
    """

    def __init__(
        self,
        text: str = "Button",
        x: float = 100.0,
        y: float = 100.0,
        w: float = 120.0,
        h: float = 40.0,
        mass: float = 1.0,
        stiffness: float = 0.1,
        z: int = 0,
        css_classes: Optional[List[str]] = None,
        on_click: Optional[str] = None,
    ):
        classes = (css_classes or []) + ["aether-button"]
        styles = {
            "background": "rgba(99, 102, 241, 0.2)",
            "border": "1px solid rgba(99, 102, 241, 0.4)",
            "border-radius": "8px",
            "color": "#e0e0e0",
            "font-size": "14px",
            "cursor": "pointer",
            "will-change": "transform",
        }
        super().__init__(x, y, w, h, color=(0.3, 0.3, 0.6, 0.9), z=z,
                         html_tag="button", css_classes=classes, styles=styles)
        self._text = text
        self._mass = mass
        self._stiffness = stiffness
        if on_click:
            self._styles["data-on-click"] = on_click

    @property
    def html_metadata(self) -> Dict[str, Any]:
        meta = super().html_metadata
        meta["text"] = self._text
        return meta


class WebText(WebElement):
    """
    HTML text element with physics positioning.

    Renders as a <span> or <p> element. Text is selectable in the browser.
    """

    def __init__(
        self,
        text: str = "Text",
        x: float = 100.0,
        y: float = 100.0,
        w: float = 200.0,
        h: float = 30.0,
        font_size: int = 14,
        font_family: str = "system-ui, sans-serif",
        color=(0.9, 0.9, 0.9, 1.0),
        z: int = 0,
    ):
        styles = {
            "font-size": f"{font_size}px",
            "font-family": font_family,
            "color": f"rgba({int(color[0]*255)}, {int(color[1]*255)}, {int(color[2]*255)}, {color[3]})",
            "line-height": "1.4",
            "will-change": "transform",
        }
        super().__init__(x, y, w, h, color=color, z=z,
                         html_tag="span", css_classes=["aether-text"], styles=styles)
        self._text = text

    @property
    def html_metadata(self) -> Dict[str, Any]:
        meta = super().html_metadata
        meta["text"] = self._text
        return meta


class WebCard(WebElement):
    """
    HTML container card with physics properties.

    Renders as a <div> with rounded corners and background. Acts as a
    parent container for child elements.
    """

    def __init__(
        self,
        title: str = "Card",
        x: float = 100.0,
        y: float = 100.0,
        w: float = 300.0,
        h: float = 200.0,
        mass: float = 1.5,
        stiffness: float = 0.08,
        z: int = 0,
        css_classes: Optional[List[str]] = None,
    ):
        classes = (css_classes or []) + ["aether-card"]
        styles = {
            "background": "rgba(15, 23, 42, 0.85)",
            "border": "1px solid rgba(99, 102, 241, 0.2)",
            "border-radius": "12px",
            "backdrop-filter": "blur(10px)",
            "box-shadow": "0 4px 20px rgba(0, 0, 0, 0.3)",
            "will-change": "transform",
        }
        super().__init__(x, y, w, h, color=(0.1, 0.1, 0.2, 0.9), z=z,
                         html_tag="div", css_classes=classes, styles=styles)
        self._title = title
        self._mass = mass
        self._stiffness = stiffness

    @property
    def html_metadata(self) -> Dict[str, Any]:
        meta = super().html_metadata
        meta["text"] = self._title
        return meta


class WebInput(WebElement):
    """
    Native HTML input element with physics positioning.

    Renders as an <input> element. User input is captured natively by
    the browser and can be read back by the Python engine.
    """

    def __init__(
        self,
        placeholder: str = "Type here...",
        input_type: str = "text",
        x: float = 100.0,
        y: float = 100.0,
        w: float = 200.0,
        h: float = 36.0,
        z: int = 0,
        css_classes: Optional[List[str]] = None,
    ):
        classes = (css_classes or []) + ["aether-input"]
        styles = {
            "background": "rgba(30, 30, 50, 0.9)",
            "border": "1px solid rgba(99, 102, 241, 0.3)",
            "border-radius": "6px",
            "color": "#e0e0e0",
            "padding": "8px 12px",
            "font-size": "14px",
            "outline": "none",
            "will-change": "transform",
        }
        super().__init__(x, y, w, h, color=(0.2, 0.2, 0.3, 0.9), z=z,
                         html_tag="input", css_classes=classes, styles=styles)
        self._placeholder = placeholder
        self._input_type = input_type
        self._value = ""

    @property
    def html_metadata(self) -> Dict[str, Any]:
        meta = super().html_metadata
        meta["placeholder"] = self._placeholder
        meta["input_type"] = self._input_type
        meta["value"] = self._value
        return meta
