"""
Numba-optimized solver for Aetheris UI.
Uses @njit for maximum desktop performance.

Aether-Guard: Includes L2 Norm clamping and NaN protection.
"""
import numpy as np
from numba import njit


@njit(cache=True)
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
    mag = np.float64(0.0)
    for i in range(len(vector)):
        mag += vector[i] * vector[i]
    mag = np.sqrt(mag)
    
    if mag > max_val and mag > 1e-9:
        scale = max_val / mag
        result = np.empty(len(vector), dtype=vector.dtype)
        for i in range(len(vector)):
            result[i] = np.float32(vector[i] * scale)
        return result
    
    return vector


@njit(cache=True)
def calculate_restoring_force(current_state: np.ndarray, target_state: np.ndarray, spring_constant: float) -> np.ndarray:
    """
    Applies Hooke's law to pull an element toward its target asymptote.
    current_state and target_state are [x, y, w, h].
    Formula: Force = (target - current) * spring_constant
    
    Aether-Guard: Clamps spring_constant to [0, 10000] and force magnitude to 10000.
    """
    # Aether-Guard: Clamp spring_constant to safe range
    # Practical infinity check: values > 1e15 are treated as infinite
    if spring_constant < 0.0 or spring_constant > 1e15:
        spring_constant = 0.1  # Safe default for invalid values
    
    error = target_state - current_state
    force = (error * spring_constant).astype(np.float32)
    
    # Aether-Guard: Clamp force magnitude (max 10000 for safety)
    return clamp_vector_magnitude(force, 10000.0)


@njit(cache=True)
def calculate_boundary_forces(state: np.ndarray, container_w: float, container_h: float, boundary_stiffness: float) -> np.ndarray:
    """
    Calculates repulsion forces if the element crosses container boundaries.
    state is [x, y, w, h].
    
    Aether-Guard: Clamps boundary force magnitude to prevent explosions.
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


@njit(cache=True)
def lerp_arrays(state_a: np.ndarray, state_b: np.ndarray, t: float) -> np.ndarray:
    """
    Vectorized Linear Interpolation for high-dimensional arrays.
    Numba-optimized version.
    
    Formula: result = (1-t) * a + t * b
    """
    result = np.empty(4, dtype=np.float32)
    for i in range(4):
        result[i] = np.float32((1.0 - t) * state_a[i] + t * state_b[i])
    return result


@njit(cache=True)
def speed_to_stiffness(transition_time_ms: float) -> float:
    """
    Derive Spring Constant (k) from transition duration (T).
    Numba-optimized version.
    
    Formula: k = 16 / T^2 (T in seconds)
    """
    if transition_time_ms <= 0.0:
        return 0.1
    
    T_sec = transition_time_ms / 1000.0
    if T_sec < 0.001:
        T_sec = 0.001
    
    k = 16.0 / (T_sec * T_sec)
    return np.float32(min(k, 10000.0))


@njit(cache=True)
def speed_to_viscosity(transition_time_ms: float) -> float:
    """
    Derive optimal viscosity from transition speed.
    Numba-optimized version.
    """
    if transition_time_ms <= 0.0:
        return 0.1
    
    viscosity = 1.0 - (transition_time_ms / 1000.0)
    return np.float32(max(0.05, min(viscosity, 0.95)))
