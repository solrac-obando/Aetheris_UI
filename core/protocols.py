# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Protocol definitions for Aetheris.

These Protocols provide structural typing (duck typing) for type checkers
while maintaining full backward compatibility with existing code.
"""

from typing import Protocol, runtime_checkable, Any, Self
import numpy as np


@runtime_checkable
class Renderable(Protocol):
    """Protocol for elements that can be rendered."""
    
    @property
    def state(self) -> np.ndarray:
        """Return the element's state array."""
        ...
    
    def render(self, data: np.ndarray) -> None:
        """Render the element with given data."""
        ...


@runtime_checkable  
class PhysicsBody(Protocol):
    """Protocol for elements with physics simulation."""
    
    @property
    def position(self) -> tuple[float, float]:
        """Return (x, y) position."""
        ...
    
    @property
    def velocity(self) -> tuple[float, float]:
        """Return (vx, vy) velocity."""
        ...
    
    def apply_force(self, force: tuple[float, float]) -> None:
        """Apply a force vector to the element."""
        ...


@runtime_checkable
class Interactive(Protocol):
    """Protocol for interactive elements that respond to input."""
    
    def on_click(self, x: float, y: float) -> None:
        """Handle click event at coordinates."""
        ...
    
    def on_hover(self, x: float, y: float) -> None:
        """Handle hover event at coordinates."""
        ...
    
    def on_drag(self, dx: float, dy: float) -> None:
        """Handle drag event with delta."""
        ...


@runtime_checkable
class StateContainer(Protocol):
    """Protocol for elements that hold state."""
    
    @property
    def state(self) -> np.ndarray:
        """Return current state."""
        ...
    
    @state.setter
    def state(self, value: np.ndarray) -> None:
        """Set new state."""
        ...


@runtime_checkable
class Serializable(Protocol):
    """Protocol for elements that can be serialized."""
    
    def to_dict(self) -> dict[str, Any]:
        """Convert element to dictionary."""
        ...
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create element from dictionary."""
        ...


@runtime_checkable
class Clonable(Protocol):
    """Protocol for elements that can be cloned."""
    
    def clone(self) -> Self:
        """Create a deep copy of the element."""
        ...


@runtime_checkable
class Disposable(Protocol):
    """Protocol for elements that need cleanup."""
    
    def dispose(self) -> None:
        """Clean up resources."""
        ...
    
    @property
    def disposed(self) -> bool:
        """Check if element has been disposed."""
        ...


# Type aliases using protocols
RenderableList = list[Renderable]
PhysicsBodyList = list[PhysicsBody]
InteractiveList = list[Interactive]

__all__ = [
    "Renderable",
    "PhysicsBody", 
    "Interactive",
    "StateContainer",
    "Serializable",
    "Clonable",
    "Disposable",
    "RenderableList",
    "PhysicsBodyList", 
    "InteractiveList",
]
