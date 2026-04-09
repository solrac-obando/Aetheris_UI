# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from core.layout.parser import ElementNode, parse_layout_dsl
from core.elements import (
    DifferentialElement, StaticBox, SmartPanel, SmartButton,
    FlexibleTextNode, CanvasTextNode, DOMTextNode
)


class LayoutCompiler:
    ELEMENT_TYPE_MAP = {
        "box": StaticBox,
        "panel": SmartPanel,
        "button": SmartButton,
        "text": FlexibleTextNode,
        "canvas_text": CanvasTextNode,
        "dom_text": DOMTextNode,
    }

    def __init__(self):
        self._element_counter = 0

    def compile(self, ast_nodes: List[ElementNode], container_w: float = 800, container_h: float = 600) -> List[DifferentialElement]:
        elements = []
        for node in ast_nodes:
            element = self._compile_element(node, container_w, container_h)
            if element:
                elements.append(element)
        return elements

    def _compile_element(self, node: ElementNode, container_w: float, container_h: float, parent: Optional[DifferentialElement] = None) -> Optional[DifferentialElement]:
        element_type = node.type.lower()
        element_class = self.ELEMENT_TYPE_MAP.get(element_type)

        if not element_class:
            return None

        props = node.properties

        if element_class == SmartButton:
            if parent is None:
                parent = StaticBox(x=0, y=0, w=container_w, h=container_h)
            offset_x = props.get("offset_x", 0)
            offset_y = props.get("offset_y", 0)
            offset_w = props.get("width", 100)
            offset_h = props.get("height", 50)
            color = self._parse_color(props.get("color", (0.8, 0.8, 0.2, 1.0)))
            z = props.get("z", 0)
            sound_trigger = props.get("sound_trigger", None)
            return SmartButton(parent, offset_x, offset_y, offset_w, offset_h, color, z, sound_trigger)

        elif element_class == SmartPanel:
            padding = props.get("padding", 0.05)
            color = self._parse_color(props.get("color", (1, 1, 1, 1)))
            z = props.get("z", 0)
            sound_trigger = props.get("sound_trigger", None)
            return SmartPanel(x=0, y=0, w=100, h=100, color=color, z=z, padding=padding, sound_trigger=sound_trigger)

        elif element_class == StaticBox:
            x = props.get("x", 0)
            y = props.get("y", 0)
            w = props.get("width", 100)
            h = props.get("height", 100)
            color = self._parse_color(props.get("color", (1, 1, 1, 1)))
            z = props.get("z", 0)
            sound_trigger = props.get("sound_trigger", None)
            return StaticBox(x, y, w, h, color, z, sound_trigger)

        elif element_class == FlexibleTextNode:
            x = props.get("x", 0)
            y = props.get("y", 0)
            w = props.get("width", 200)
            h = props.get("height", 50)
            color = self._parse_color(props.get("color", (1, 1, 1, 1)))
            z = props.get("z", 0)
            text = props.get("text", "Text")
            sound_trigger = props.get("sound_trigger", None)
            return FlexibleTextNode(x, y, w, h, color, z, text, sound_trigger)

        elif element_class == CanvasTextNode:
            x = props.get("x", 0)
            y = props.get("y", 0)
            w = props.get("width", 200)
            h = props.get("height", 50)
            color = self._parse_color(props.get("color", (1, 1, 1, 1)))
            z = props.get("z", 0)
            text = props.get("text", "Text")
            font_size = props.get("font_size", 24)
            font_family = props.get("font_family", "Arial")
            sound_trigger = props.get("sound_trigger", None)
            return CanvasTextNode(x, y, w, h, color, z, text, font_size, font_family, sound_trigger)

        elif element_class == DOMTextNode:
            x = props.get("x", 0)
            y = props.get("y", 0)
            w = props.get("width", 200)
            h = props.get("height", 50)
            color = self._parse_color(props.get("color", (0, 0, 0, 0)))
            z = props.get("z", 0)
            text = props.get("text", "Text")
            font_size = props.get("font_size", 16)
            font_family = props.get("font_family", "Arial")
            text_color = self._parse_color(props.get("text_color", (1, 1, 1, 1)))
            sound_trigger = props.get("sound_trigger", None)
            return DOMTextNode(x, y, w, h, color, z, text, font_size, font_family, text_color, sound_trigger)

        return None

    def _parse_color(self, color_value: Any) -> Tuple[float, float, float, float]:
        if isinstance(color_value, (list, tuple)) and len(color_value) >= 4:
            return (float(color_value[0]), float(color_value[1]), float(color_value[2]), float(color_value[3]))
        if isinstance(color_value, str):
            if color_value.startswith("#"):
                hex_color = color_value[1:]
                if len(hex_color) == 6:
                    r = int(hex_color[0:2], 16) / 255.0
                    g = int(hex_color[2:4], 16) / 255.0
                    b = int(hex_color[4:6], 16) / 255.0
                    return (r, g, b, 1.0)
                elif len(hex_color) == 8:
                    r = int(hex_color[0:2], 16) / 255.0
                    g = int(hex_color[2:4], 16) / 255.0
                    b = int(hex_color[4:6], 16) / 255.0
                    a = int(hex_color[6:8], 16) / 255.0
                    return (r, g, b, a)
        return (1.0, 1.0, 1.0, 1.0)


class FlexboxMapper:
    def __init__(self, container_w: float = 800, container_h: float = 600):
        self.container_w = container_w
        self.container_h = container_h

    def map_to_flex(self, element: DifferentialElement, layout_type: str = "column") -> Dict[str, Any]:
        props = {}
        if layout_type == "row":
            props["flex_direction"] = "row"
        elif layout_type == "column":
            props["flex_direction"] = "column"
        elif layout_type == "grid":
            props["flex_direction"] = "grid"
        return props


class PhysicsCompiler:
    DEFAULT_STIFFNESS = 0.1
    DEFAULT_DAMPING = 0.8

    def compile_physics(self, element: DifferentialElement, physics_config: Dict[str, Any]) -> None:
        if hasattr(element, "tensor") and element.tensor:
            pass

    def parse_physics_string(self, physics_str: str) -> Dict[str, Any]:
        result = {"stiffness": self.DEFAULT_STIFFNESS, "damping": self.DEFAULT_DAMPING}
        if not physics_str:
            return result
        if "spring" in physics_str:
            match = re.search(r"k\s*=\s*([0-9.]+)", physics_str)
            if match:
                result["stiffness"] = float(match.group(1))
            match = re.search(r"damping\s*=\s*([0-9.]+)", physics_str)
            if match:
                result["damping"] = float(match.group(1))
        return result


import re