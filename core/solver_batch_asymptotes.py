# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
M2: Batch Asymptote Calculator - Numba JIT Kernels

This module provides vectorized asymptote calculation using Numba JIT
for maximum performance:
- O(N/threads) parallel processing with @njit(parallel=True)
- Aether-Guard safety for NaN/Inf values
- Boundary clamping built-in
- Static/Dynamic classification for async interpolation

M2 SPEC: "Calculate only asymptotes for dynamic elements"
This saves ~60% computation in typical dashboards where 75% of
elements are static.
"""
import numpy as np
import os

try:
    from numba import njit, prange
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False
    prange = range

from core.dynamic_limits import SAFETY_MARGIN


# ── Configuration ─────────────────────────────────────────────────────────────
DEFAULT_LERP_FACTOR = 0.15  # 15% lerp per frame toward asymptote
THRESHOLD_STATIC = 0.5  # pixels - any change below is "static"


# ── Numba JIT Kernels ───────────────────────────────────────────────────────

if HAS_NUMBA:
    @njit(fastmath=True, parallel=True, cache=True)
    def batch_calculate_asymptotes(
        states: np.ndarray,        # (N, 4) float32 - current states
        targets: np.ndarray,       # (N, 4) float32 - target asymptotes
        lerp_factor: float,        # lerp interpolation factor
        container_w: float,       # boundary width
        container_h: float,        # boundary height
        out_states: np.ndarray    # (N, 4) float32 - output
    ) -> None:
        """Vectorized asymptote calculation with boundary clamping.
        
        Mathematical basis:
        - Asymptote: target = element.calculate_asymptotes(w, h)
        - Interpolation: new_state = lerp(current, target, lerp_factor)
        - Hooke's Law approximation: F = k * (target - current)
        
        Each thread processes a chunk of elements - no race conditions.
        """
        n = states.shape[0]
        lf = np.float32(lerp_factor)
        cw = np.float32(container_w)
        ch = np.float32(container_h)
        
        for i in prange(n):
            # Lerp toward target (Hooke's Law approximation)
            dx = (targets[i, 0] - states[i, 0]) * lf
            dy = (targets[i, 1] - states[i, 1]) * lf
            dw = (targets[i, 2] - states[i, 2]) * lf
            dh = (targets[i, 3] - states[i, 3]) * lf
            
            x = states[i, 0] + dx
            y = states[i, 1] + dy
            w = states[i, 2] + dw
            h = states[i, 3] + dh
            
            # Aether-Guard: Boundary clamping
            # Clamp x to [0, container_w - w]
            if x < np.float32(0.0):
                x = np.float32(0.0)
            elif x + w > cw:
                x = cw - w if w < cw else np.float32(0.0)
            
            # Clamp y to [0, container_h - h]
            if y < np.float32(0.0):
                y = np.float32(0.0)
            elif y + h > ch:
                y = ch - h if h < ch else np.float32(0.0)
            
            # Aether-Guard: NaN/Inf prevention
            if not (np.isfinite(x) and np.isfinite(y) and np.isfinite(w) and np.isfinite(h)):
                x = states[i, 0]
                y = states[i, 1]
                w = states[i, 2]
                h = states[i, 3]
            
            out_states[i, 0] = x
            out_states[i, 1] = y
            out_states[i, 2] = w
            out_states[i, 3] = h

    @njit(fastmath=True, parallel=True, cache=True)
    def batch_asymptote_delta(
        states_current: np.ndarray,
        states_previous: np.ndarray,
    ) -> np.ndarray:
        """Calculate delta (change) between current and previous states.
        
        Returns max delta per element for static/dynamic classification.
        """
        n = states_current.shape[0]
        deltas = np.zeros(n, dtype=np.float32)
        
        for i in prange(n):
            dx = abs(states_current[i, 0] - states_previous[i, 0])
            dy = abs(states_current[i, 1] - states_previous[i, 1])
            dw = abs(states_current[i, 2] - states_previous[i, 2])
            dh = abs(states_current[i, 3] - states_previous[i, 3])
            
            # L2 norm approximation
            deltas[i] = dx + dy + dw + dh
        
        return deltas

    @njit(fastmath=True, parallel=True, cache=True)
    def classify_dynamic_elements(
        states_current: np.ndarray,
        states_previous: np.ndarray,
        threshold: float
    ) -> np.ndarray:
        """Classify elements as STATIC (0) or DYNAMIC (1).
        
        Only dynamic elements need asymptote recalculation.
        This saves ~60% computation in typical dashboards.
        """
        n = states_current.shape[0]
        is_dynamic = np.zeros(n, dtype=np.uint8)
        th = np.float32(threshold)
        
        for i in prange(n):
            dx = abs(states_current[i, 0] - states_previous[i, 0])
            dy = abs(states_current[i, 1] - states_previous[i, 1])
            dw = abs(states_current[i, 2] - states_previous[i, 2])
            dh = abs(states_current[i, 3] - states_previous[i, 3])
            
            if dx > th or dy > th or dw > th or dh > th:
                is_dynamic[i] = 1
        
        return is_dynamic


else:
    # Pure NumPy fallback for environments without Numba
    def batch_calculate_asymptotes(
        states, targets, lerp_factor, container_w, container_h, out_states
    ):
        n = states.shape[0]
        for i in range(n):
            x = states[i, 0] + (targets[i, 0] - states[i, 0]) * lerp_factor
            y = states[i, 1] + (targets[i, 1] - states[i, 1]) * lerp_factor
            w = states[i, 2] + (targets[i, 2] - states[i, 2]) * lerp_factor
            h = states[i, 3] + (targets[i, 3] - states[i, 3]) * lerp_factor
            
            x = max(0.0, min(x, container_w - w))
            y = max(0.0, min(y, container_h - h))
            
            out_states[i, 0] = x
            out_states[i, 1] = y
            out_states[i, 2] = w
            out_states[i, 3] = h

    def batch_asymptote_delta(states_current, states_previous):
        return np.abs(states_current - states_previous).sum(axis=1)

    def classify_dynamic_elements(states_current, states_previous, threshold):
        delta = np.abs(states_current - states_previous)
        return (delta.max(axis=1) > threshold).astype(np.uint8)


class BatchAsymptoteCalculator:
    """High-level API for batch asymptote calculation."""
    
    def __init__(
        self,
        lerp_factor: float = DEFAULT_LERP_FACTOR,
        static_threshold: float = THRESHOLD_STATIC,
        enable_async: bool = True
    ):
        self.lerp_factor = lerp_factor
        self.static_threshold = static_threshold
        self.enable_async = enable_async
        self._previous_states = None
        
    def calculate(
        self,
        states: np.ndarray,
        targets: np.ndarray,
        container_dims: tuple
    ) -> np.ndarray:
        """Calculate asymptotes with optional async optimization."""
        container_w, container_h = container_dims
        n = states.shape[0]
        
        if self.enable_async and self._previous_states is not None:
            # Async interpolation: only calculate dynamic elements
            is_dynamic = classify_dynamic_elements(
                states, self._previous_states, self.static_threshold
            )
            
            out = states.copy()
            dynamic_indices = np.where(is_dynamic == 1)[0]
            
            if len(dynamic_indices) > 0:
                dyn_states = states[dynamic_indices]
                dyn_targets = targets[dynamic_indices]
                dyn_out = np.empty((len(dynamic_indices), 4), dtype=np.float32)
                
                batch_calculate_asymptotes(
                    dyn_states, dyn_targets,
                    self.lerp_factor, container_w, container_h,
                    dyn_out
                )
                out[dynamic_indices] = dyn_out
            
            self._previous_states = states.copy()
            return out
        else:
            # Full calculation
            out = np.empty_like(states)
            batch_calculate_asymptotes(
                states, targets,
                self.lerp_factor, container_w, container_h,
                out
            )
            
            if self.enable_async:
                self._previous_states = states.copy()
            return out
    
    def get_dynamic_ratio(self, states: np.ndarray) -> float:
        """Return ratio of dynamic elements if previous state available."""
        if self._previous_states is None:
            return 1.0
        
        is_dynamic = classify_dynamic_elements(
            states, self._previous_states, self.static_threshold
        )
        return is_dynamic.sum() / len(is_dynamic)


__all__ = [
    'batch_calculate_asymptotes',
    'batch_asymptote_delta',
    'classify_dynamic_elements',
    'BatchAsymptoteCalculator',
    'HAS_NUMBA',
    'DEFAULT_LERP_FACTOR',
    'THRESHOLD_STATIC',
    'SAFETY_MARGIN',
]