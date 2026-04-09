# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

from typing import Optional, Dict, Any, Tuple, Type
import numpy as np
from core.elements import (
    DifferentialElement, StaticBox, SmartPanel, SmartButton,
    FlexibleTextNode, CanvasTextNode, DOMTextNode
)


class ElementFactory:
    ELEMENT_REGISTRY: Dict[str, Type[DifferentialElement]] = {
        "box": StaticBox,
        "panel": SmartPanel,
        "button": SmartButton,
        "smartbutton": SmartButton,
        "text": FlexibleTextNode,
        "canvas_text": CanvasTextNode,
        "dom_text": DOMTextNode,
        "staticbox": StaticBox,
        "smartpanel": SmartPanel,
    }

    @classmethod
    def create(cls, element_type: str, **kwargs) -> Optional[DifferentialElement]:
        element_class = cls.ELEMENT_REGISTRY.get(element_type.lower())
        if not element_class:
            return None

        if element_class == SmartButton:
            parent = kwargs.pop("parent", None)
            if parent is None:
                parent = StaticBox(x=0, y=0, w=800, h=600)
            return SmartButton(
                parent,
                kwargs.get("offset_x", 0),
                kwargs.get("offset_y", 0),
                kwargs.get("offset_w", 100),
                kwargs.get("offset_h", 50),
                kwargs.get("color", (0.8, 0.8, 0.2, 1.0)),
                kwargs.get("z", 0),
                kwargs.get("sound_trigger", None)
            )

        elif element_class == SmartPanel:
            return SmartPanel(
                x=kwargs.get("x", 0),
                y=kwargs.get("y", 0),
                w=kwargs.get("w", 100),
                h=kwargs.get("h", 100),
                color=kwargs.get("color", (1, 1, 1, 1)),
                z=kwargs.get("z", 0),
                padding=kwargs.get("padding", 0.05),
                sound_trigger=kwargs.get("sound_trigger", None)
            )

        elif element_class == StaticBox:
            return StaticBox(
                x=kwargs.get("x", 0),
                y=kwargs.get("y", 0),
                w=kwargs.get("w", 100),
                h=kwargs.get("h", 100),
                color=kwargs.get("color", (1, 1, 1, 1)),
                z=kwargs.get("z", 0),
                sound_trigger=kwargs.get("sound_trigger", None)
            )

        elif element_class == FlexibleTextNode:
            return FlexibleTextNode(
                x=kwargs.get("x", 0),
                y=kwargs.get("y", 0),
                w=kwargs.get("w", 200),
                h=kwargs.get("h", 50),
                color=kwargs.get("color", (1, 1, 1, 1)),
                z=kwargs.get("z", 0),
                text=kwargs.get("text", "Text"),
                sound_trigger=kwargs.get("sound_trigger", None)
            )

        elif element_class == CanvasTextNode:
            return CanvasTextNode(
                x=kwargs.get("x", 0),
                y=kwargs.get("y", 0),
                w=kwargs.get("w", 200),
                h=kwargs.get("h", 50),
                color=kwargs.get("color", (1, 1, 1, 1)),
                z=kwargs.get("z", 0),
                text=kwargs.get("text", "Text"),
                font_size=kwargs.get("font_size", 24),
                font_family=kwargs.get("font_family", "Arial"),
                sound_trigger=kwargs.get("sound_trigger", None)
            )

        elif element_class == DOMTextNode:
            return DOMTextNode(
                x=kwargs.get("x", 0),
                y=kwargs.get("y", 0),
                w=kwargs.get("w", 200),
                h=kwargs.get("h", 50),
                color=kwargs.get("color", (0, 0, 0, 0)),
                z=kwargs.get("z", 0),
                text=kwargs.get("text", "Text"),
                font_size=kwargs.get("font_size", 16),
                font_family=kwargs.get("font_family", "Arial"),
                text_color=kwargs.get("text_color", (1, 1, 1, 1)),
                sound_trigger=kwargs.get("sound_trigger", None)
            )

        return None

    @classmethod
    def register(cls, name: str, element_class: Type[DifferentialElement]) -> None:
        cls.ELEMENT_REGISTRY[name.lower()] = element_class

    @classmethod
    def get_available_types(cls) -> list:
        return list(cls.ELEMENT_REGISTRY.keys())


class AutoSizer:
    @staticmethod
    def calculate_size(element_type: str, container_w: float, container_h: float, params: Dict[str, Any]) -> Tuple[float, float, float, float]:
        if element_type == "panel":
            padding = params.get("padding", 0.05)
            x = container_w * padding
            y = container_h * padding
            w = container_w * (1.0 - 2.0 * padding)
            h = container_h * (1.0 - 2.0 * padding)
            return (x, y, w, h)

        elif element_type == "button":
            w = params.get("width", 100)
            h = params.get("height", 50)
            return (0, 0, w, h)

        elif element_type == "text":
            text_length = len(params.get("text", "Text"))
            w = max(text_length * 10, 50)
            h = params.get("height", 30)
            return (0, 0, w, h)

        w = params.get("width", 100)
        h = params.get("height", 100)
        return (params.get("x", 0), params.get("y", 0), w, h)