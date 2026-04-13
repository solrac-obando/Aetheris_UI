# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Type stubs for Aetheris core module.

These stubs provide type hints for IDEs and type checkers
without modifying the runtime code.
"""

from typing import Any, TypedDict

class ElementConfig(TypedDict, total=False):
    """Configuration for UI elements."""
    x: float
    y: float
    w: float
    h: float
    color: tuple[float, float, float, float]
    z_index: int
    metadata: dict[str, Any]

class RenderData(TypedDict):
    """Data returned from engine.tick()"""
    x: float
    y: float
    w: float
    h: float
    r: float
    g: float
    b: float
    a: float
    z: int
