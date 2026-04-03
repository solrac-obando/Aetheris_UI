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
    
    Aether-Guard: Clamps force magnitude to prevent explosive values.
    """
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
