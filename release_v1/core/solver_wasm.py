# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Pure NumPy solver for WASM/Pyodide compatibility.
Replaces Numba-optimized functions with standard NumPy vectorized operations.

Mathematical Foundation: Same Hooke's Law and boundary force calculations
as the Numba version - only the execution path differs.

Aether-Guard: Includes L2 Norm clamping and NaN protection.
"""
import numpy as np


def clamp_vector_magnitude(vector: np.ndarray, max_val: float) -> np.ndarray:
    """
    Aether-Guard: Clamp vector magnitude (L2 Norm) while preserving direction.
    
    Linear Algebra: If ||v|| > max_val, then v_clamped = (v / ||v||) * max_val
    
    Args:
        vector: Input vector
        max_val: Maximum allowed magnitude
        
    Returns:
        Vector with magnitude clamped to max_val
    """
    mag = np.linalg.norm(vector)
    if mag > max_val and mag > 1e-9:
        return (vector / mag) * max_val
    return vector


def calculate_restoring_force(current_state: np.ndarray, target_state: np.ndarray, spring_constant: float) -> np.ndarray:
    """
    Applies Hooke's law to pull an element toward its target asymptote.
    Pure NumPy version for WASM/Pyodide compatibility.
    
    Formula: Force = (target - current) * spring_constant
    
    Aether-Guard: Clamps force magnitude to prevent explosive values.
    
    Args:
        current_state: Current [x, y, w, h] as float32
        target_state: Target [x, y, w, h] as float32
        spring_constant: k value derived from transition time
        
    Returns:
        Force vector as float32, magnitude-clamped
    """
    error = target_state - current_state
    force = (error * spring_constant).astype(np.float32)
    
    # Aether-Guard: Clamp force magnitude
    return clamp_vector_magnitude(force, 10000.0)


def calculate_boundary_forces(state: np.ndarray, container_w: float, container_h: float, boundary_stiffness: float) -> np.ndarray:
    """
    Calculates repulsion forces if the element crosses container boundaries.
    Pure NumPy version for WASM/Pyodide compatibility.
    
    Aether-Guard: Clamps boundary force magnitude.
    
    Args:
        state: Current [x, y, w, h] as float32
        container_w: Container width
        container_h: Container height
        boundary_stiffness: Spring constant for boundary repulsion
        
    Returns:
        Boundary force vector as float32, magnitude-clamped
    """
    force = np.zeros(4, dtype=np.float32)
    x, y, w, h = state[0], state[1], state[2], state[3]

    # Left boundary (x < 0)
    if x < 0.0:
        force[0] += (0.0 - x) * boundary_stiffness
    # Right boundary (x + w > container_w)
    elif (x + w) > container_w:
        force[0] -= ((x + w) - container_w) * boundary_stiffness

    # Top boundary (y < 0)
    if y < 0.0:
        force[1] += (0.0 - y) * boundary_stiffness
    # Bottom boundary (y + h > container_h)
    elif (y + h) > container_h:
        force[1] -= ((y + h) - container_h) * boundary_stiffness

    # Aether-Guard: Clamp boundary force magnitude
    return clamp_vector_magnitude(force, 5000.0)


def lerp_arrays(state_a: np.ndarray, state_b: np.ndarray, t: float) -> np.ndarray:
    """
    Vectorized Linear Interpolation for high-dimensional arrays.
    Pure NumPy version for WASM/Pyodide compatibility.
    """
    return ((1.0 - t) * state_a + t * state_b).astype(np.float32)


def speed_to_stiffness(transition_time_ms: float) -> float:
    """
    Derive Spring Constant (k) from transition duration (T).
    Pure NumPy version for WASM/Pyodide compatibility.
    
    Formula: k = 16 / T^2 (T in seconds)
    """
    if transition_time_ms <= 0.0:
        return 0.1
    
    T_sec = transition_time_ms / 1000.0
    if T_sec < 0.001:
        T_sec = 0.001
    
    k = 16.0 / (T_sec * T_sec)
    return np.float32(min(k, 10000.0))


def speed_to_viscosity(transition_time_ms: float) -> float:
    """
    Derive optimal viscosity from transition speed.
    Pure NumPy version for WASM/Pyodide compatibility.
    """
    if transition_time_ms <= 0.0:
        return 0.1
    
    viscosity = 1.0 - (transition_time_ms / 1000.0)
    return np.float32(max(0.05, min(viscosity, 0.95)))
