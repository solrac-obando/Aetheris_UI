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
    from core.solver import (
        calculate_restoring_force,
        calculate_boundary_forces,
        lerp_arrays,
        speed_to_stiffness,
        speed_to_viscosity,
    )
    HAS_NUMBA = True
except (ImportError, ModuleNotFoundError):
    # Fallback to pure NumPy implementation for WASM/Pyodide
    from core.solver_wasm import (
        calculate_restoring_force,
        calculate_boundary_forces,
        lerp_arrays,
        speed_to_stiffness,
        speed_to_viscosity,
    )
    HAS_NUMBA = False

__all__ = [
    'calculate_restoring_force',
    'calculate_boundary_forces',
    'lerp_arrays',
    'speed_to_stiffness',
    'speed_to_viscosity',
    'HAS_NUMBA',
]
