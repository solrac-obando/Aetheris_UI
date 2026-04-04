# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

import numpy as np
import warnings


# ============================================================================
# AETHER-GUARD: Mathematical Safety Layer
# ============================================================================
# Constants for numerical stability
EPSILON = np.float32(1e-9)
MAX_VELOCITY = np.float32(5000.0)       # pixels/sec
MAX_ACCELERATION = np.float32(10000.0)  # pixels/sec²
SNAP_DISTANCE = np.float32(0.5)          # pixels
SNAP_VELOCITY = np.float32(5.0)          # pixels/sec


def safe_divide(numerator, denominator, epsilon=EPSILON):
    """
    Safe division with epsilon protection.
    
    Mathematical Foundation (Cálculo - Límites):
    Ensures no denominator is ever smaller than epsilon to prevent
    division-by-zero or infinity results.
    
    lim(x->0) f(x)/x is undefined, so we use:
    f(x) / max(|x|, epsilon) * sign(x)
    
    Args:
        numerator: Dividend (scalar or array)
        denominator: Divisor (scalar or array)
        epsilon: Minimum absolute value for denominator
        
    Returns:
        Safe division result, never inf or NaN from zero division
    """
    denom = np.maximum(np.abs(denominator), epsilon)
    sign = np.sign(denominator)
    # When sign is 0 (denominator was exactly 0), use 1.0 to avoid zeroing the result
    safe_sign = np.where(sign == 0, 1.0, sign)
    return numerator / (denom * safe_sign)


def clamp_magnitude(vector, max_val):
    """
    Clamp the L2 norm (magnitude) of a vector while preserving direction.
    
    Linear Algebra Foundation (Vector Normalization):
    If ||v|| > max_val, then v_clamped = (v / ||v||) * max_val
    
    This preserves the direction of the vector while limiting its magnitude,
    preventing explosive velocities in the physics simulation.
    
    Args:
        vector: numpy array representing a vector
        max_val: Maximum allowed magnitude
        
    Returns:
        Clamped vector with magnitude <= max_val
    """
    mag = np.linalg.norm(vector)
    if mag > max_val and mag > EPSILON:
        return (vector / mag) * max_val
    return vector


def check_and_fix_nan(array, name="tensor"):
    """
    Check for NaN values and fix them gracefully.
    
    If NaN is detected, logs a warning and returns a zeroed array
    instead of propagating the NaN through the simulation.
    
    Args:
        array: numpy array to check
        name: Name for logging purposes
        
    Returns:
        Original array if clean, zeroed array if NaN detected
    """
    if np.any(np.isnan(array)) or np.any(np.isinf(array)):
        warnings.warn(
            f"Aether-Guard: NaN/Inf detected in {name}. Resetting to zero.",
            RuntimeWarning
        )
        return np.zeros_like(array, dtype=array.dtype)
    return array


class StateTensor:
    """Aetheris UI treats UI elements as physical particles.

    Each element has a state vector [x, y, width, height] and evolves
    through velocity and acceleration using Euler integration with
    viscosity (friction) for stability.
    
    Aether-Guard safety features:
    - Epsilon-protected division
    - L2 Norm velocity/acceleration clamping
    - NaN/Inf detection and graceful recovery
    - UI Snap Threshold (99% Rule)
    """

    def __init__(self, x: float = 0.0, y: float = 0.0, w: float = 100.0, h: float = 100.0):
        # Initialize the 3 core vectors as float32 for OpenGL compatibility
        self.state = np.array([x, y, w, h], dtype=np.float32)
        self.velocity = np.zeros(4, dtype=np.float32)
        self.acceleration = np.zeros(4, dtype=np.float32)

    def apply_force(self, force: np.ndarray):
        """Apply a force vector to acceleration.

        Assumes mass m=1, so F = ma becomes F = a.
        Force adds to existing acceleration (forces accumulate).
        
        Aether-Guard: Clamps acceleration magnitude to prevent explosions.
        """
        safe_force = check_and_fix_nan(force.astype(np.float32), "force")
        self.acceleration += safe_force
        
        # L2 Norm clamping for acceleration
        self.acceleration = clamp_magnitude(self.acceleration, MAX_ACCELERATION)

    def euler_integrate(self, dt: float, viscosity: float = 0.1, target_state: np.ndarray = None):
        """Update physics state using Euler integration.

        1. Aether-Guard: Validate dt with safe_divide
        2. Update velocity with acceleration and apply friction (viscosity)
        3. Aether-Guard: Clamp velocity magnitude (L2 Norm)
        4. Update position state based on velocity
        5. Clamp width and height to prevent negative dimensions
        6. Reset acceleration to zero for next frame
        7. Aether-Guard: Check for NaN/Inf in state and velocity
        8. Apply UI Snap Threshold (99% Rule): if close enough to target, snap
        """
        # Aether-Guard: Validate dt
        safe_dt = float(safe_divide(np.float32(dt), np.float32(1.0)))
        safe_dt = max(safe_dt, 0.0)  # No negative time
        safe_dt = min(safe_dt, 1.0)   # Cap dt to prevent huge jumps (1s max)
        
        # 1. Update velocity with friction: v_new = (v + a * dt) * (1 - viscosity)
        self.velocity = (self.velocity + self.acceleration * safe_dt) * np.float32(1.0 - viscosity)
        
        # 2. Aether-Guard: L2 Norm velocity clamping
        self.velocity = clamp_magnitude(self.velocity, MAX_VELOCITY)
        
        # 3. Update state: s_new = s + v * dt
        self.state = self.state + self.velocity * safe_dt

        # 4. Clamp width and height to >= 0.0 (safety constraint)
        self.state[2] = max(self.state[2], np.float32(0.0))
        self.state[3] = max(self.state[3], np.float32(0.0))

        # 5. Reset acceleration to zero (prevents infinite accumulation)
        self.acceleration.fill(np.float32(0.0))
        
        # 6. Aether-Guard: NaN/Inf detection and recovery
        self.state = check_and_fix_nan(self.state, "state")
        self.velocity = check_and_fix_nan(self.velocity, "velocity")
        
        # 7. Apply UI Snap Threshold (99% Rule/Epsilon Snapping)
        if target_state is not None:
            # Calculate distance to target (L2 norm of position and size differences)
            distance = np.linalg.norm(self.state - target_state)
            # Velocity magnitude
            velocity_magnitude = np.linalg.norm(self.velocity)
            
            # Snap conditions: within 0.5 pixels AND moving slowly (< 5.0 px/s)
            if distance < SNAP_DISTANCE and velocity_magnitude < SNAP_VELOCITY:
                self.state = target_state.copy()
                self.velocity.fill(np.float32(0.0))
                # Note: acceleration is already zero from line above
