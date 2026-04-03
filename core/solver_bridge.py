"""
Dual-path solver module for Aetheris UI.
Automatically selects Numba-optimized or Pure NumPy implementation
based on environment availability.

Desktop: Uses @njit-optimized functions from solver.py
WASM/Pyodide: Falls back to pure NumPy functions from solver_wasm.py
"""
import numpy as np

# Attempt to import Numba-optimized solver
try:
    from numba import njit
    from core.solver import calculate_restoring_force, calculate_boundary_forces
    HAS_NUMBA = True
except (ImportError, ModuleNotFoundError):
    # Fallback to pure NumPy implementation for WASM/Pyodide
    from core.solver_wasm import calculate_restoring_force, calculate_boundary_forces
    HAS_NUMBA = False

# Attempt to import Numba-optimized state manager functions
try:
    from core.state_manager import lerp_arrays
except (ImportError, ModuleNotFoundError):
    from core.solver_wasm import lerp_arrays

# Attempt to import Numba-optimized tensor compiler functions
try:
    from core.tensor_compiler import speed_to_stiffness, speed_to_viscosity
except (ImportError, ModuleNotFoundError):
    from core.solver_wasm import speed_to_stiffness, speed_to_viscosity

__all__ = [
    'calculate_restoring_force',
    'calculate_boundary_forces',
    'lerp_arrays',
    'speed_to_stiffness',
    'speed_to_viscosity',
    'HAS_NUMBA',
]
