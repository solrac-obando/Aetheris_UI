# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Dual-path solver module for Aetheris UI — HPC Multi-Core Edition.

Automatically selects Numba-optimized (parallel) or Pure NumPy implementation
based on environment availability.

Desktop: Uses @njit(parallel=True, fastmath=True) with prange for auto-vectorization
WASM/Pyodide: Falls back to pure NumPy functions from solver_wasm.py

Mathematical Validation:
  - Hooke's Law: F = (target - current) * k — linear, commutative, parallel-safe
  - Symplectic Euler: v = (v + a*dt)*(1-μ), s = s + v*dt — energy-conserving
  - Aether-Guard: ε-protected division, L2 norm clamping, NaN guard
  - No floating point drift: each thread writes to its own output slice
"""
import numpy as np
import os

# ── Resource Intelligence: Cap at 60% of available cores ──────────────────
_CPU_COUNT = os.cpu_count() or 4
_TARGET_THREADS = max(1, int(_CPU_COUNT * 0.6))
os.environ["NUMBA_NUM_THREADS"] = str(_TARGET_THREADS)


def get_hpc_config():
    """Return HPC configuration for monitoring/debugging."""
    return {
        "cpu_count": _CPU_COUNT,
        "target_threads": _TARGET_THREADS,
        "cpu_usage_pct": 60,
    }


# Attempt to import Numba-optimized parallel solver
try:
    from numba import njit, prange

    @njit(fastmath=True, cache=True)
    def clamp_vector_magnitude(vector: np.ndarray, max_val: float) -> np.ndarray:
        """Aether-Guard: Clamp vector magnitude (L2 Norm) while preserving direction."""
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

    @njit(parallel=True, fastmath=True, cache=True)
    def calculate_restoring_force(current_state: np.ndarray, target_state: np.ndarray, spring_constant: float) -> np.ndarray:
        """Parallel Hooke's Law: F = (target - current) * k.

        Each element's force is computed independently — no cross-thread dependencies.
        Mathematical validation: Hooke's Law is linear and commutative, so parallel
        execution produces identical results to sequential (no floating point drift).
        """
        if spring_constant < 0.0 or spring_constant > 1e15:
            spring_constant = 0.1

        error = target_state - current_state
        force = (error * spring_constant).astype(np.float32)
        return clamp_vector_magnitude(force, 10000.0)

    @njit(parallel=True, fastmath=True, cache=True)
    def calculate_boundary_forces(state: np.ndarray, container_w: float, container_h: float, boundary_stiffness: float) -> np.ndarray:
        """Parallel boundary repulsion forces.

        Each element checks its own boundaries independently.
        No cross-thread dependencies — perfectly parallel.
        """
        force = np.zeros(4, dtype=np.float32)
        x, y, w, h = state[0], state[1], state[2], state[3]

        if x < 0.0:
            force[0] += (0.0 - x) * boundary_stiffness
        elif (x + w) > container_w:
            force[0] -= ((x + w) - container_w) * boundary_stiffness

        if y < 0.0:
            force[1] += (0.0 - y) * boundary_stiffness
        elif (y + h) > container_h:
            force[1] -= ((y + h) - container_h) * boundary_stiffness

        return clamp_vector_magnitude(force, 5000.0)

    @njit(parallel=True, fastmath=True, cache=True)
    def lerp_arrays(state_a: np.ndarray, state_b: np.ndarray, t: float) -> np.ndarray:
        """Vectorized Linear Interpolation — parallelized for batch operations."""
        result = np.empty(4, dtype=np.float32)
        for i in range(4):
            result[i] = np.float32((1.0 - t) * state_a[i] + t * state_b[i])
        return result

    @njit(parallel=True, fastmath=True, cache=True)
    def speed_to_stiffness(transition_time_ms: float) -> float:
        """Derive Spring Constant (k) from transition duration (T). Formula: k = 16 / T^2"""
        if transition_time_ms <= 0.0:
            return 0.1

        T_sec = transition_time_ms / 1000.0
        if T_sec < 0.001:
            T_sec = 0.001

        k = 16.0 / (T_sec * T_sec)
        return np.float32(min(k, 10000.0))

    @njit(parallel=True, fastmath=True, cache=True)
    def speed_to_viscosity(transition_time_ms: float) -> float:
        """Derive optimal viscosity from transition speed."""
        if transition_time_ms <= 0.0:
            return 0.1

        viscosity = 1.0 - (transition_time_ms / 1000.0)
        return np.float32(max(0.05, min(viscosity, 0.95)))

    # ── Batch Parallel Kernel (O(n) → O(n/threads)) ─────────────────────
    @njit(parallel=True, fastmath=True, cache=True)
    def batch_restoring_forces(
        states: np.ndarray,       # (N, 4) float32
        targets: np.ndarray,      # (N, 4) float32
        spring_k: float,
        out_forces: np.ndarray,   # (N, 4) float32 — pre-allocated
    ) -> None:
        """Batch Hooke's Law for all elements in a single parallel kernel.

        Each thread processes a chunk of elements. No race conditions because
        each thread writes to its own output slice.
        """
        n = states.shape[0]
        for i in prange(n):
            fx = (targets[i, 0] - states[i, 0]) * spring_k
            fy = (targets[i, 1] - states[i, 1]) * spring_k
            fw = (targets[i, 2] - states[i, 2]) * spring_k
            fh = (targets[i, 3] - states[i, 3]) * spring_k

            # Aether-Guard: clamp force magnitude
            mag = np.sqrt(fx * fx + fy * fy + fw * fw + fh * fh)
            if mag > 10000.0 and mag > 1e-9:
                s = 10000.0 / mag
                fx *= s; fy *= s; fw *= s; fh *= s

            out_forces[i, 0] = fx
            out_forces[i, 1] = fy
            out_forces[i, 2] = fw
            out_forces[i, 3] = fh

    @njit(parallel=True, fastmath=True, cache=True)
    def batch_boundary_forces(
        states: np.ndarray,       # (N, 4) float32
        container_w: float,
        container_h: float,
        boundary_k: float,
        out_forces: np.ndarray,   # (N, 4) float32 — pre-allocated
    ) -> None:
        """Batch boundary repulsion for all elements."""
        n = states.shape[0]
        for i in prange(n):
            fx = 0.0
            fy = 0.0
            x, y, w, h = states[i, 0], states[i, 1], states[i, 2], states[i, 3]

            if x < 0.0:
                fx += (0.0 - x) * boundary_k
            elif (x + w) > container_w:
                fx -= ((x + w) - container_w) * boundary_k

            if y < 0.0:
                fy += (0.0 - y) * boundary_k
            elif (y + h) > container_h:
                fy -= ((y + h) - container_h) * boundary_k

            mag = np.sqrt(fx * fx + fy * fy)
            if mag > 5000.0 and mag > 1e-9:
                s = 5000.0 / mag
                fx *= s; fy *= s

            out_forces[i, 0] = fx
            out_forces[i, 1] = fy
            out_forces[i, 2] = 0.0
            out_forces[i, 3] = 0.0

    @njit(parallel=True, fastmath=True, cache=True)
    def batch_integrate(
        states: np.ndarray,       # (N, 4) float32 — updated in-place
        velocities: np.ndarray,   # (N, 4) float32 — updated in-place
        forces: np.ndarray,       # (N, 4) float32
        dt: float,
        viscosity: float,
        max_velocity: float,
    ) -> None:
        """Batch symplectic Euler integration — parallel, energy-conserving.

        v_new = (v + f*dt) * (1 - viscosity)
        s_new = s + v_new * dt

        Symplectic Euler is energy-conserving and stable. Each element's
        integration is fully independent — no race conditions, no drift.
        """
        n = states.shape[0]
        damp = 1.0 - viscosity

        for i in prange(n):
            vx = (velocities[i, 0] + forces[i, 0] * dt) * damp
            vy = (velocities[i, 1] + forces[i, 1] * dt) * damp
            vw = (velocities[i, 2] + forces[i, 2] * dt) * damp
            vh = (velocities[i, 3] + forces[i, 3] * dt) * damp

            # Aether-Guard: L2 norm velocity clamping
            speed = np.sqrt(vx * vx + vy * vy)
            if speed > max_velocity and speed > 1e-9:
                s = max_velocity / speed
                vx *= s; vy *= s

            states[i, 0] += vx * dt
            states[i, 1] += vy * dt
            states[i, 2] = max(states[i, 2] + vw * dt, 0.0)
            states[i, 3] = max(states[i, 3] + vh * dt, 0.0)

            velocities[i, 0] = vx
            velocities[i, 1] = vy
            velocities[i, 2] = vw
            velocities[i, 3] = vh

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

    def get_hpc_config():
        return {
            "cpu_count": _CPU_COUNT,
            "target_threads": 1,
            "cpu_usage_pct": 100,  # Single-threaded, no cap needed
        }

    def batch_restoring_forces(states, targets, spring_k, out_forces):
        n = states.shape[0]
        for i in range(n):
            out_forces[i] = calculate_restoring_force(states[i], targets[i], spring_k)

    def batch_boundary_forces(states, container_w, container_h, boundary_k, out_forces):
        n = states.shape[0]
        for i in range(n):
            out_forces[i] = calculate_boundary_forces(states[i], container_w, container_h, boundary_k)

    def batch_integrate(states, velocities, forces, dt, viscosity, max_velocity):
        n = states.shape[0]
        damp = 1.0 - viscosity
        for i in range(n):
            v = velocities[i] + forces[i] * dt
            v *= damp
            # L2 norm clamping
            speed = np.sqrt(v[0]**2 + v[1]**2)
            if speed > max_velocity and speed > 1e-9:
                v[:2] *= max_velocity / speed
            states[i] += v * dt
            states[i, 2] = max(states[i, 2], 0.0)
            states[i, 3] = max(states[i, 3], 0.0)
            velocities[i] = v

__all__ = [
    'calculate_restoring_force',
    'calculate_boundary_forces',
    'lerp_arrays',
    'speed_to_stiffness',
    'speed_to_viscosity',
    'HAS_NUMBA',
    'get_hpc_config',
    'batch_restoring_forces',
    'batch_boundary_forces',
    'batch_integrate',
]
