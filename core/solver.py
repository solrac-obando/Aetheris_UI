import numpy as np
from numba import njit


@njit(cache=True)
def calculate_restoring_force(current_state: np.ndarray, target_state: np.ndarray, spring_constant: float) -> np.ndarray:
    """
    Applies Hooke's law to pull an element toward its target asymptote.
    current_state and target_state are [x, y, w, h].
    Formula: Force = (target - current) * spring_constant
    """
    # Ensure output is float32
    error = target_state - current_state
    return (error * spring_constant).astype(np.float32)


@njit(cache=True)
def calculate_boundary_forces(state: np.ndarray, container_w: float, container_h: float, boundary_stiffness: float) -> np.ndarray:
    """
    Calculates repulsion forces if the element crosses container boundaries.
    state is [x, y, w, h].
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

    return force
