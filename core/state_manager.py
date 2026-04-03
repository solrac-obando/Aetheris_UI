import numpy as np
from numba import njit


@njit(cache=True)
def lerp_arrays(state_a: np.ndarray, state_b: np.ndarray, t: float) -> np.ndarray:
    """Vectorized Linear Interpolation for high-dimensional arrays."""
    return (1.0 - t) * state_a + t * state_b


class StateManager:
    def __init__(self):
        self.last_width = 0
        self.last_height = 0
        self.hyper_damping_frames = 0
        
    def check_teleportation_shock(self, current_w: int, current_h: int) -> float:
        """Calculates if a drastic resolution change occurred (Delta > 200px)."""
        if self.last_width == 0:
            self.last_width, self.last_height = current_w, current_h
            return 1.0
            
        delta_w = abs(current_w - self.last_width)
        self.last_width, self.last_height = current_w, current_h
        
        if delta_w > 200:
            self.hyper_damping_frames = 15 # Absorb shock for 15 frames
            
        if self.hyper_damping_frames > 0:
            self.hyper_damping_frames -= 1
            return 5.0 # 5x viscosity
            
        return 1.0
    
    def lerp_arrays(self, state_a, state_b, t):
        return lerp_arrays(state_a, state_b, t)