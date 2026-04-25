# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Input Manager v2.0 - Multi-Touch & Advanced Gestures.

Bridges user pointer/touch input to the physics solver.
Supports: Drag, Drop, Throw, Pinch-to-Zoom, Multi-finger Pan, and Swipe.

Mathematical Foundation:
- Throw & Swipe velocity: Second-Order Backward Difference.
- Pinch Scale: ΔDistance / InitialDistance
- Panning: ΔCentroid
"""
import numpy as np
import time
from collections import deque
from typing import Optional, Tuple, Dict, List, Any


class InputManager:
    """Manages pointer state and translates it into physics forces and gestures.
    
    Now supports multiple concurrent pointers for mobile-style interactions.
    """
    
    # Physics constants for drag interaction
    DRAG_STIFFNESS = 5.0
    DRAG_DAMPING = 0.3
    THROW_VELOCITY_SCALE = 1.0
    
    # Gesture constants
    SWIPE_THRESHOLD_VEL = 500.0  # px/s
    KINETIC_FRICTION = 0.95      # Velocity multiplier per frame
    
    # History buffer size for velocity calculation
    HISTORY_SIZE = 10
    
    def __init__(self) -> None:
        self._is_dragging = False
        self._dragged_element_index: Optional[int] = None
        
        # Pointer tracking: {pointer_id: (x, y, timestamp)}
        self._pointers: Dict[int, Tuple[float, float, float]] = {}
        
        # History for gesture calculation
        self._position_history: deque = deque(maxlen=self.HISTORY_SIZE)
        
        # Gesture state
        self._initial_pinch_dist: Optional[float] = None
        self._current_scale: float = 1.0
        self._pan_offset: np.ndarray = np.zeros(2, dtype=np.float32)
        
        # Kinetic scroll state
        self._kinetic_vel: np.ndarray = np.zeros(2, dtype=np.float32)
        self._is_scrolling: bool = False

    @property
    def _pointer_x(self) -> float:
        """Compatibility for old tests."""
        if not self._pointers: return 0.0
        return self._pointers[list(self._pointers.keys())[0]][0]

    @_pointer_x.setter
    def _pointer_x(self, value: float) -> None:
        """Compatibility for old tests. Updates pointer ID 0."""
        if 0 not in self._pointers:
            self._pointers[0] = (value, 0.0, time.perf_counter())
        else:
            prev = self._pointers[0]
            self._pointers[0] = (value, prev[1], prev[2])

    @property
    def _pointer_y(self) -> float:
        """Compatibility for old tests."""
        if not self._pointers: return 0.0
        return self._pointers[list(self._pointers.keys())[0]][1]

    @_pointer_y.setter
    def _pointer_y(self, value: float) -> None:
        """Compatibility for old tests. Updates pointer ID 0."""
        if 0 not in self._pointers:
            self._pointers[0] = (0.0, value, time.perf_counter())
        else:
            prev = self._pointers[0]
            self._pointers[0] = (prev[0], value, prev[2])

    @property
    def is_dragging(self) -> bool:
        return self._is_dragging

    @property
    def dragged_element_index(self) -> Optional[int]:
        return self._dragged_element_index

    @property
    def current_scale(self) -> float:
        return self._current_scale

    @property
    def pan_offset(self) -> np.ndarray:
        return self._pan_offset

    def pointer_down(self, pointer_id: Any, x: float = 0.0, y: float = 0.0, 
                     element_index: Any = None) -> None:
        """Register a new pointer down event. Supports multi-touch and legacy API."""
        real_id = pointer_id
        real_x = x
        real_y = y
        real_idx = element_index
        ts = None

        # Legacy detection: if element_index was passed as float (likely timestamp)
        if isinstance(element_index, float):
            real_idx = pointer_id
            real_id = 0
            ts = element_index

        if ts is None:
            ts = time.perf_counter()
            
        self._pointers[real_id] = (float(real_x), float(real_y), ts)
        
        # If it's the first pointer and an element was hit, start dragging
        if len(self._pointers) == 1 and real_idx is not None:
            self._is_dragging = True
            self._dragged_element_index = real_idx
            self._position_history.clear()
            self._position_history.append((float(real_x), float(real_y), ts))
            self._is_scrolling = False
            self._kinetic_vel.fill(0)
            
        # Initialize pinch if we have 2 pointers
        if len(self._pointers) == 2:
            self._initial_pinch_dist = self._calculate_pointer_dist()
            
    def pointer_move(self, pointer_id: Any, x: float, y: Optional[float] = None, 
                     timestamp: Optional[float] = None) -> None:
        """Update pointer position and evaluate gestures.
        
        Supports:
        - New: pointer_move(id, x, y)
        - Old: pointer_move(x, y, ts)
        """
        real_id = pointer_id
        real_x = x
        real_y = y
        ts = timestamp

        # Legacy detection:
        if timestamp is not None or (y is not None and real_id not in self._pointers and 0 in self._pointers):
            real_x = pointer_id
            real_y = x
            if timestamp is not None:
                ts = timestamp
            else:
                ts = y # 3rd arg was likely ts in (x, y, ts)
            real_id = 0
            
        if real_id not in self._pointers:
            return
            
        if ts is None:
            ts = time.perf_counter()
            
        prev_x, prev_y, prev_ts = self._pointers[real_id]
        self._pointers[real_id] = (float(real_x), float(real_y), ts)
        
        # 1. Update Drag History
        if self._is_dragging and real_id == list(self._pointers.keys())[0]:
            self._position_history.append((float(real_x), float(real_y), ts))
            
        # 2. Pinch Gesture (Scale)
        if len(self._pointers) == 2 and self._initial_pinch_dist is not None:
            current_dist = self._calculate_pointer_dist()
            if self._initial_pinch_dist > 1e-3:
                self._current_scale *= (current_dist / self._initial_pinch_dist)
                self._initial_pinch_dist = current_dist  # Update for continuous scaling
                
        # 3. Pan Gesture (Two-finger pan)
        if len(self._pointers) >= 2:
            dx = float(x) - prev_x
            dy = float(y) - prev_y
            # Average movement across pointers
            self._pan_offset[0] += dx / len(self._pointers)
            self._pan_offset[1] += dy / len(self._pointers)

    def pointer_up(self, pointer_id: int) -> None:
        """Handle pointer release and detect swipes/throws."""
        if pointer_id in self._pointers:
            # Detect Swipe/Throw before removing the pointer
            if len(self._pointers) == 1 and self._is_dragging:
                vx, vy = self.get_throw_velocity()
                
                # Check for Swipe (Fast release)
                mag = np.sqrt(vx*vx + vy*vy)
                if mag > self.SWIPE_THRESHOLD_VEL:
                    self._kinetic_vel = np.array([vx, vy], dtype=np.float32)
                    self._is_scrolling = True
                
            del self._pointers[pointer_id]
            
        if not self._pointers:
            self._is_dragging = False
            self._dragged_element_index = None
            self._initial_pinch_dist = None

    def update_kinetic_scroll(self, dt: float) -> None:
        """Apply kinetic scroll inertia."""
        if not self._is_scrolling:
            return
            
        self._pan_offset[0] += self._kinetic_vel[0] * dt
        self._pan_offset[1] += self._kinetic_vel[1] * dt
        
        # Apply friction
        self._kinetic_vel *= self.KINETIC_FRICTION
        
        # Stop if velocity is low
        if np.linalg.norm(self._kinetic_vel) < 10.0:
            self._is_scrolling = False
            self._kinetic_vel.fill(0)

    def _calculate_pointer_dist(self) -> float:
        """Calculate Euclidean distance between the first two pointers."""
        keys = list(self._pointers.keys())
        p1 = self._pointers[keys[0]]
        p2 = self._pointers[keys[1]]
        return float(np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2))

    def get_throw_velocity(self) -> Tuple[float, float]:
        """Calculates velocity using 2nd-order backward difference.
        
        Falls back to 1st-order if only 2 points are available.
        """
        if len(self._position_history) < 2:
            return (0.0, 0.0)
        
        p_curr = self._position_history[-1]
        p_prev = self._position_history[-2]
        
        dt = p_curr[2] - p_prev[2]
        if dt < 1e-6:
            return (0.0, 0.0)
            
        if len(self._position_history) >= 3:
            p_prev2 = self._position_history[-3]
            # 2nd-order backward difference
            vx = (3.0 * p_curr[0] - 4.0 * p_prev[0] + p_prev2[0]) / (2.0 * dt)
            vy = (3.0 * p_curr[1] - 4.0 * p_prev[1] + p_prev2[1]) / (2.0 * dt)
        else:
            # 1st-order (fallback for legacy tests/fast interaction)
            vx = (p_curr[0] - p_prev[0]) / dt
            vy = (p_curr[1] - p_prev[1]) / dt
            
        return (vx * self.THROW_VELOCITY_SCALE, vy * self.THROW_VELOCITY_SCALE)

    def calculate_drag_force(self, ex: float, ey: float, ew: float, eh: float) -> np.ndarray:
        """Calculate spring force pulling element toward the first pointer."""
        if not self._pointers:
            return np.zeros(4, dtype=np.float32)
            
        first_ptr = self._pointers[list(self._pointers.keys())[0]]
        cx = ex + ew / 2.0
        cy = ey + eh / 2.0
        
        fx = (first_ptr[0] - cx) * self.DRAG_STIFFNESS
        fy = (first_ptr[1] - cy) * self.DRAG_STIFFNESS
        
        return np.array([fx, fy, 0.0, 0.0], dtype=np.float32)

    def reset(self) -> None:
        self._is_dragging = False
        self._dragged_element_index = None
        self._pointers.clear()
        self._position_history.clear()
        self._is_scrolling = False
        self._kinetic_vel.fill(0)
