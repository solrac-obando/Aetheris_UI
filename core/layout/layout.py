# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

from typing import List, Optional, Dict, Any
from core.layout.parser import parse_layout_dsl, ElementNode
from core.layout.compiler import LayoutCompiler, FlexboxMapper, PhysicsCompiler
from core.layout.factory import ElementFactory, AutoSizer
from core.elements import DifferentialElement


class AetherLayout:
    def __init__(self, dsl_string: str = "", container_w: float = 800, container_h: float = 600):
        self._dsl_string = dsl_string
        self._container_w = container_w
        self._container_h = container_h
        self._compiler = LayoutCompiler()
        self._flexbox_mapper = FlexboxMapper(container_w, container_h)
        self._physics_compiler = PhysicsCompiler()
        self._elements: List[DifferentialElement] = []
        self._ast_nodes: List[ElementNode] = []

        if dsl_string:
            self._parse()

    def _parse(self) -> None:
        self._ast_nodes = parse_layout_dsl(self._dsl_string)
        self._elements = self._compiler.compile(self._ast_nodes, self._container_w, self._container_h)

    def set_container_size(self, w: float, h: float) -> None:
        self._container_w = w
        self._container_h = h
        if self._dsl_string:
            self._parse()

    def get_elements(self) -> List[DifferentialElement]:
        return self._elements

    def create_element(self, element_type: str, **kwargs) -> Optional[DifferentialElement]:
        return ElementFactory.create(element_type, **kwargs)

    def add_element(self, element: DifferentialElement) -> None:
        self._elements.append(element)

    def remove_element(self, element: DifferentialElement) -> None:
        if element in self._elements:
            self._elements.remove(element)

    def get_ast(self) -> List[ElementNode]:
        return self._ast_nodes

    @staticmethod
    def from_file(file_path: str, container_w: float = 800, container_h: float = 600) -> "AetherLayout":
        with open(file_path, "r") as f:
            dsl_content = f.read()
        return AetherLayout(dsl_content, container_w, container_h)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "container_w": self._container_w,
            "container_h": self._container_h,
            "element_count": len(self._elements),
            "elements": [
                {
                    "type": type(e).__name__,
                    "rect": e.tensor.state.tolist() if hasattr(e, "tensor") and e.tensor else None,
                }
                for e in self._elements
            ]
        }