# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Input Manager - Bridges user pointer/touch input to the physics solver.

Enables Drag, Drop, and Throw mechanics by converting DOM events into
physics forces applied to specific elements.

Mathematical Foundation (Precálculo - Derivatives):
Throw velocity is calculated using Second-Order Backward Difference:
    v ≈ (3·P_current - 4·P_prev + P_prev2) / (2·dt)

This formula is more accurate than naive (P_current - P_prev) / dt
because it cancels out first-order error terms, preventing the "jittery
throw" effect common in naive implementations.
"""
import numpy as np
from collections import deque
from typing import Optional, Tuple


class InputManager:
    """Manages pointer state and translates it into physics forces.
    
    When a user drags an element, a high-stiffness spring connects the
    element's center to the mouse cursor. On release, the element's
    velocity is set based on the pointer's recent movement history,
    creating a natural "throw" effect.
    """
    
    # Physics constants for drag interaction
    DRAG_STIFFNESS = 5.0        # High stiffness for responsive dragging
    DRAG_DAMPING = 0.3          # Extra damping during drag for stability
    THROW_VELOCITY_SCALE = 1.0  # Scale factor for throw velocity
    
    # History buffer size for velocity calculation
    HISTORY_SIZE = 5
    
    def __init__(self):
        self._is_dragging = False
        self._dragged_element_index: Optional[int] = None
        self._pointer_x: float = 0.0
        self._pointer_y: float = 0.0
        
        # History for throw velocity calculation: deque of (x, y, timestamp)
        self._position_history: deque = deque(maxlen=self.HISTORY_SIZE)
    
    @property
    def is_dragging(self) -> bool:
        """Whether a drag operation is currently active."""
        return self._is_dragging
    
    @property
    def dragged_element_index(self) -> Optional[int]:
        """Index of the element being dragged, or None."""
        return self._dragged_element_index
    
    def pointer_down(self, element_index: int, x: float, y: float, timestamp: float) -> None:
        """
        Start a drag operation on the specified element.
        
        Args:
            element_index: Index of the element in the engine's registry
            x: Pointer X position in screen coordinates
            y: Pointer Y position in screen coordinates
            timestamp: Current time in seconds (for velocity calculation)
        """
        self._is_dragging = True
        self._dragged_element_index = element_index
        self._pointer_x = float(x)
        self._pointer_y = float(y)
        
        # Clear history and start fresh
        self._position_history.clear()
        self._position_history.append((float(x), float(y), float(timestamp)))
    
    def pointer_move(self, x: float, y: float, timestamp: float) -> None:
        """
        Update pointer position during drag.
        
        Args:
            x: Pointer X position in screen coordinates
            y: Pointer Y position in screen coordinates
            timestamp: Current time in seconds
        """
        self._pointer_x = float(x)
        self._pointer_y = float(y)
        self._position_history.append((float(x), float(y), float(timestamp)))
    
    def pointer_up(self) -> None:
        """End the drag operation."""
        self._is_dragging = False
        self._dragged_element_index = None
    
    def get_throw_velocity(self) -> Tuple[float, float]:
        """
        Calculate throw velocity using Second-Order Backward Difference.
        
        Formula: v ≈ (3·P_current - 4·P_prev + P_prev2) / (2·dt)
        
        This is a second-order accurate approximation of the derivative,
        which means the error is O(dt²) instead of O(dt) for the naive
        forward difference. This prevents the "jittery throw" effect
        because it smooths out high-frequency noise in the pointer data.
        
        Why it works:
        - Naive: v = (P_n - P_{n-1}) / dt — amplifies noise, jittery
        - 2nd-order: v = (3·P_n - 4·P_{n-1} + P_{n-2}) / (2·dt) — cancels
          first-order error, smooth result
        
        Returns:
            Tuple of (vx, vy) throw velocity in pixels/second.
        """
        if len(self._position_history) < 3:
            # Not enough history for 2nd-order formula, fall back to naive
            if len(self._position_history) >= 2:
                curr = self._position_history[-1]
                prev = self._position_history[-2]
                dt = curr[2] - prev[2]
                if dt > 1e-6:
                    return (
                        (curr[0] - prev[0]) / dt * self.THROW_VELOCITY_SCALE,
                        (curr[1] - prev[1]) / dt * self.THROW_VELOCITY_SCALE,
                    )
            return (0.0, 0.0)
        
        # Second-Order Backward Difference
        p_curr = self._position_history[-1]
        p_prev = self._position_history[-2]
        p_prev2 = self._position_history[-3]
        
        dt = p_curr[2] - p_prev[2]
        if dt < 1e-6:
            return (0.0, 0.0)
        
        # v = (3·P_n - 4·P_{n-1} + P_{n-2}) / (2·dt)
        vx = (3.0 * p_curr[0] - 4.0 * p_prev[0] + p_prev2[0]) / (2.0 * dt)
        vy = (3.0 * p_curr[1] - 4.0 * p_prev[1] + p_prev2[1]) / (2.0 * dt)
        
        return (
            vx * self.THROW_VELOCITY_SCALE,
            vy * self.THROW_VELOCITY_SCALE,
        )
    
    def calculate_drag_force(self, element_x: float, element_y: float,
                              element_w: float, element_h: float) -> np.ndarray:
        """
        Calculate the drag force pulling an element toward the pointer.
        
        Formula: F_drag = (PointerPos - ElementCenter) × k_drag
        
        Args:
            element_x: Element X position
            element_y: Element Y position
            element_w: Element width
            element_h: Element height
            
        Returns:
            Force vector [fx, fy, 0, 0] as float32
        """
        # Calculate element center
        center_x = element_x + element_w / 2.0
        center_y = element_y + element_h / 2.0
        
        # Spring force toward pointer position
        fx = (self._pointer_x - center_x) * self.DRAG_STIFFNESS
        fy = (self._pointer_y - center_y) * self.DRAG_STIFFNESS
        
        return np.array([fx, fy, 0.0, 0.0], dtype=np.float32)
    
    def reset(self) -> None:
        """Reset all input state."""
        self._is_dragging = False
        self._dragged_element_index = None
        self._pointer_x = 0.0
        self._pointer_y = 0.0
        self._position_history.clear()
