"""
State Manager with dual-path execution for WASM/Pyodide compatibility.
Falls back to pure NumPy when Numba is unavailable.
"""
import numpy as np

try:
    from numba import njit
    HAS_NUMBA = True
except (ImportError, ModuleNotFoundError):
    HAS_NUMBA = False


if HAS_NUMBA:
    @njit(cache=True)
    def _lerp_arrays(state_a: np.ndarray, state_b: np.ndarray, t: float) -> np.ndarray:
        """Vectorized Linear Interpolation (Numba-optimized)."""
        result = np.empty(4, dtype=np.float32)
        for i in range(4):
            result[i] = np.float32((1.0 - t) * state_a[i] + t * state_b[i])
        return result
else:
    def _lerp_arrays(state_a: np.ndarray, state_b: np.ndarray, t: float) -> np.ndarray:
        """Vectorized Linear Interpolation (Pure NumPy)."""
        return ((1.0 - t) * state_a + t * state_b).astype(np.float32)


class StateManager:
    def __init__(self):
        self.last_width = 0
        self.last_height = 0
        self.hyper_damping_frames = 0
        
    def check_teleportation_shock(self, current_w: int, current_h: int) -> float:
        """
        Calculates if a drastic resolution change occurred.
        Returns a viscosity multiplier (e.g., 1.0 for normal, 5.0 for shock absorption).
        """
        if self.last_width == 0:
            self.last_width, self.last_height = current_w, current_h
            return 1.0
            
        delta_w = abs(current_w - self.last_width)
        self.last_width, self.last_height = current_w, current_h
        
        if delta_w > 200:
            self.hyper_damping_frames = 15
            
        if self.hyper_damping_frames > 0:
            self.hyper_damping_frames -= 1
            return 5.0
            
        return 1.0
    
    def lerp_arrays(self, state_a, state_b, t):
        return _lerp_arrays(state_a, state_b, t)
