# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Type definitions using TypedDict for Aetheris.

These classes provide type-safe configuration for UI elements
without affecting runtime performance.
"""

from typing import TypedDict, NotRequired, Literal, Any

class Position2D(TypedDict):
    """2D position coordinates."""
    x: float
    y: float

class Size2D(TypedDict):
    """2D size dimensions."""
    w: float
    h: float

class ColorRGBA(TypedDict):
    """RGBA color values (0-1)."""
    r: float
    g: float
    b: float
    a: float

class ElementConfig(TypedDict, total=False):
    """Base configuration for UI elements."""
    position: Position2D
    size: Size2D
    color: ColorRGBA
    z_index: int
    metadata: dict[str, any]

class SmartPanelConfig(ElementConfig):
    """Configuration for SmartPanel elements."""
    padding: float
    stiffness: float
    damping: float

class StaticBoxConfig(ElementConfig):
    """Configuration for StaticBox elements."""
    border_width: float
    border_color: ColorRGBA
    fill_color: ColorRGBA

class TextConfig(ElementConfig):
    """Configuration for text elements."""
    content: str
    font_size: float
    font_family: str
    color: ColorRGBA

class AnimationConfig(TypedDict):
    """Animation configuration."""
    type: Literal["spring", "ease", "linear", "bounce"]
    duration: float
    stiffness: float
    damping: float

class LayoutConfig(TypedDict):
    """Layout configuration for UIBuilder."""
    layout: Literal["column", "row", "grid", "absolute"]
    spacing: float
    padding: float
    animation: AnimationConfig

class SyncPayload(TypedDict):
    """Payload for WebBridge sync."""
    elements: list[dict[str, Any]]
    timestamp: float
    frame: int

class DBColumnMapping(TypedDict):
    """Database column mapping for DataBridge."""
    source: str
    scale: list[float]
    offset: NotRequired[float]
    transform: NotRequired[Literal["linear", "log", "exp"]]

class TemplateConfig(TypedDict):
    """Template configuration for UIBuilder."""
    type: str
    columns: dict[str, DBColumnMapping]
    metadata_fields: list[str]

__all__ = [
    "Position2D",
    "Size2D", 
    "ColorRGBA",
    "ElementConfig",
    "SmartPanelConfig",
    "StaticBoxConfig",
    "TextConfig",
    "AnimationConfig",
    "LayoutConfig",
    "SyncPayload",
    "DBColumnMapping",
    "TemplateConfig",
]
