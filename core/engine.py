# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

import time
import json
import os
import numpy as np
from typing import List, Optional
from core.aether_math import StateTensor
from core.elements import DifferentialElement, CanvasTextNode, DOMTextNode
from core import solver_bridge as solver
from core.state_manager import StateManager
from core.json_utils import to_json
from core.tensor_compiler import TensorCompiler
from core.input_manager import InputManager


# ── HPC Resource Throttle: Target 60-70% CPU utilization ──────────────────
_HPC_TARGET_FRAME_MS = 16.667  # 60 FPS budget
_HPC_CPU_TARGET = 0.60         # 60% of available cores
_HPC_THROTTLE_ENABLED = True   # Set False to disable throttle (tests set this to False)

# ── Dynamic Limits: Auto-detect based on hardware ─────────────────────────
try:
    from core.dynamic_limits import get_optimal_max_elements, get_system_profile
    _SYSTEM_PROFILE = get_system_profile()
    _DEFAULT_MAX_ELEMENTS = _SYSTEM_PROFILE["engine_limit"]
    _IS_SAFETY_MODE = _SYSTEM_PROFILE["safety_mode"]
    _IS_PERFORMANCE_MODE = _SYSTEM_PROFILE["performance_mode"]
except ImportError:
    _DEFAULT_MAX_ELEMENTS = int(os.environ.get("AETHERIS_MAX_ELEMENTS", "4000"))
    _IS_SAFETY_MODE = False
    _IS_PERFORMANCE_MODE = False

# ── Security Limits: Prevent DoS attacks ─────────────────────────────────────────
_MAX_ELEMENTS = int(os.environ.get("AETHERIS_MAX_ELEMENTS", str(_DEFAULT_MAX_ELEMENTS)))
_CIRCUIT_BREAKER_THRESHOLD_MS = 100  # Circuit breaker if tick exceeds 100ms
_ELEMENT_LIMIT_ENABLED = os.environ.get("AETHERIS_ELEMENT_LIMIT", "false").lower() == "true"


def _hpc_throttle(tick_start: float, tick_end: float) -> None:
    """Dynamic sleep throttle to keep CPU at ~60-70%.

    If the tick finishes faster than the proportional share of the frame budget,
    sleep for the remaining time. This prevents the engine from consuming 100%
    of CPU when the physics workload is light.

    Formula: sleep_time = (frame_budget * cpu_target) - actual_tick_time
    """
    if not _HPC_THROTTLE_ENABLED:
        return

    actual_ms = (tick_end - tick_start) * 1000.0
    target_ms = _HPC_TARGET_FRAME_MS * _HPC_CPU_TARGET

    if actual_ms < target_ms:
        sleep_sec = (target_ms - actual_ms) / 1000.0
        if sleep_sec > 1e-6:
            time.sleep(sleep_sec)


# Odyssey constants
GENRE_ORBIT_STIFFNESS = 0.05
SUPERNOVA_FORCE = 100_000.0


class AetherEngine:
    def __init__(self):
        self._elements: List[DifferentialElement] = []
        self._last_time = time.perf_counter()
        self._dt = 0.0
        self.state_manager = StateManager()
        self.tensor_compiler = TensorCompiler()
        self.input_manager = InputManager()
        self._physics_coefficients: Optional[np.ndarray] = None
        self._default_stiffness = 0.1
        self._default_viscosity = 0.1
        self._default_boundary_padding = np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32)
        self._default_spacing = 0.0
        self._audio_bridge = None
        # HPC batch buffers (pre-allocated for zero-allocation tick)
        self._batch_states: Optional[np.ndarray] = None
        self._batch_velocities: Optional[np.ndarray] = None
        self._batch_targets: Optional[np.ndarray] = None
        self._batch_forces: Optional[np.ndarray] = None
        self._batch_dirty = True
        
        # M16: Status arrays (vectorized status tracking)
        self._static_mask: Optional[np.ndarray] = None
        self._sleep_mask: Optional[np.ndarray] = None
        self._sleep_epsilons: Optional[np.ndarray] = None

    @property
    def audio_bridge(self):
        return self._audio_bridge

    @audio_bridge.setter
    def audio_bridge(self, bridge):
        self._audio_bridge = bridge

    def _ensure_batch_buffers(self, n: int) -> None:
        """Allocate or resize batch buffers for parallel kernels."""
        if self._batch_states is None or self._batch_states.shape[0] != n:
            self._batch_states = np.zeros((n, 4), dtype=np.float32)
            self._batch_velocities = np.zeros((n, 4), dtype=np.float32)
            self._batch_targets = np.zeros((n, 4), dtype=np.float32)
            self._batch_forces = np.zeros((n, 4), dtype=np.float32)
            self._batch_dirty = True
            
            # HPC Categorization (M16)
            self._static_mask = np.zeros(n, dtype=bool)
            self._sleep_mask = np.zeros(n, dtype=bool)
            self._sleep_epsilons = np.zeros(n, dtype=np.float32)
            
            for i, elem in enumerate(self._elements):
                self._static_mask[i] = getattr(elem, 'is_static', False)
                self._sleep_epsilons[i] = getattr(elem, 'sleep_epsilon', 0.05)

    def _sync_to_batch(self) -> None:
        """Copy StateTensor data into batch arrays for parallel processing.

        Aether-Guard: Sanitizes NaN/Inf values during copy to prevent
        floating point contamination in parallel kernels.
        """
        for i, elem in enumerate(self._elements):
            for j in range(4):
                v = float(elem.tensor.state[j])
                if np.isnan(v) or np.isinf(v):
                    elem.tensor.state[j] = np.float32(0.0)
                    elem.tensor.velocity[j] = np.float32(0.0)
                v = float(elem.tensor.velocity[j])
                if np.isnan(v) or np.isinf(v):
                    elem.tensor.velocity[j] = np.float32(0.0)
            self._batch_states[i] = elem.tensor.state
            self._batch_velocities[i] = elem.tensor.velocity

    def _sync_from_batch(self) -> None:
        """Write batch results back to StateTensors (thread-safe: single-threaded write-back)."""
        for i, elem in enumerate(self._elements):
            elem.tensor.state[:] = self._batch_states[i]
            elem.tensor.velocity[:] = self._batch_velocities[i]
        
    def register_element(self, element: DifferentialElement) -> None:
        if _ELEMENT_LIMIT_ENABLED and len(self._elements) >= _MAX_ELEMENTS:
            raise RuntimeError(
                f"Security: Maximum element limit ({_MAX_ELEMENTS}) exceeded. "
                f"Rejecting element to prevent DoS attack."
            )
        self._elements.append(element)
    
    def register(self, element: DifferentialElement) -> None:
        """Alias for register_element() for backwards compatibility."""
        self.register_element(element)
    
    def remove_element(self, element: DifferentialElement) -> None:
        """Remove an element from the engine."""
        if element in self._elements:
            self._elements.remove(element)
    
    def remove(self, element: DifferentialElement) -> None:
        """Alias for remove_element() for backwards compatibility."""
        self.remove_element(element)
        
    def register_state(self, name: str, state_data: dict) -> None:
        pass
        
    def transition_to(self, state_name: str) -> None:
        pass
    
    def handle_pointer_down(self, x: float, y: float) -> int:
        """
        Handle pointer/touch down event. Finds element under cursor and starts drag.
        
        Args:
            x: Pointer X position in screen coordinates
            y: Pointer Y position in screen coordinates
            
        Returns:
            Index of grabbed element, or -1 if none found.
        """
        # Hit test: find element under pointer (reverse order for z-index priority)
        for idx in range(len(self._elements) - 1, -1, -1):
            elem = self._elements[idx]
            rect = elem.tensor.state
            ex, ey, ew, eh = float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])
            
            if ex <= x <= ex + ew and ey <= y <= ey + eh:
                import time
                self.input_manager.pointer_down(idx, x, y, time.perf_counter())
                return idx
        
        return -1
    
    def handle_pointer_move(self, x: float, y: float) -> None:
        """
        Handle pointer/touch move event during drag.
        
        Args:
            x: Pointer X position in screen coordinates
            y: Pointer Y position in screen coordinates
        """
        if self.input_manager.is_dragging:
            import time
            self.input_manager.pointer_move(x, y, time.perf_counter())
    
    def handle_pointer_up(self) -> None:
        """Handle pointer/touch up event. Ends drag and applies throw velocity."""
        if self.input_manager.is_dragging and self.input_manager.dragged_element_index is not None:
            idx = self.input_manager.dragged_element_index
            if 0 <= idx < len(self._elements):
                # Apply throw velocity to the element
                vx, vy = self.input_manager.get_throw_velocity()
                self._elements[idx].tensor.velocity[0] = np.float32(vx)
                self._elements[idx].tensor.velocity[1] = np.float32(vy)
        
        self.input_manager.pointer_up()
        
    def tick(self, win_w: float, win_h: float) -> np.ndarray:
        tick_start = time.perf_counter()
        current_time = time.perf_counter()
        self._dt = current_time - self._last_time
        self._last_time = current_time

        n_elements = len(self._elements)
        if n_elements == 0:
            return np.zeros(0, dtype=[('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')])

        # Circuit Breaker: If tick is too slow, skip expensive operations
        if n_elements > _MAX_ELEMENTS // 2:
            _circuit_breaker_tripped = True
        else:
            _circuit_breaker_tripped = False

        # Phase 10: Check for layout shock (Window teleportation)
        viscosity_multiplier = self.state_manager.check_teleportation_shock(win_w, win_h)
        base_viscosity = self._default_viscosity
        active_viscosity = min(base_viscosity * viscosity_multiplier, 1.0)

        # Audio trigger evaluation (before physics integration)
        if self._audio_bridge is not None:
            for element in self._elements:
                if element._sound_trigger is not None:
                    element.evaluate_sound_trigger(self._audio_bridge)

        # Use batch parallel kernels for 10+ elements
        use_batch = solver.HAS_NUMBA and n_elements >= 10

        if use_batch:
            self._ensure_batch_buffers(n_elements)

            states_view = self._batch_states[:n_elements]
            velocities_view = self._batch_velocities[:n_elements]

            # 1. Selective Sync (Baldor Principles: Eliminate redundant group movements)
            # Only sync elements that are NOT static. Static objects are immutable in the physics loop.
            non_static_indices = np.where(~self._static_mask[:n_elements])[0]
            pending_accel_mask = np.zeros(n_elements, dtype=bool)
            
            for i in non_static_indices:
                elem = self._elements[i]
                states_view[i] = elem.tensor.state
                velocities_view[i] = elem.tensor.velocity
                if np.any(elem.tensor.acceleration != 0):
                    pending_accel_mask[i] = True

            # 2. Vectorized Sleep Check (M16/Precálculo: v^2 < eps^2)
            v_sq = (velocities_view[:, 0]**2 + velocities_view[:, 1]**2)
            
            # Additional wake up: Being dragged
            drag_mask = np.zeros(n_elements, dtype=bool)
            if self.input_manager.is_dragging and self.input_manager.dragged_element_index is not None:
                drag_idx = self.input_manager.dragged_element_index
                if 0 <= drag_idx < n_elements:
                    drag_mask[drag_idx] = True

            # Un elemento solo puede dormir si (vel < eps) Y NO tiene aceleración pendiente Y NO es arrastrado
            # Baldor: "La inercia se rompe con cualquier término de fuerza o interacción externa"
            self._sleep_mask[:n_elements] = (v_sq < self._sleep_epsilons[:n_elements]**2) & (~pending_accel_mask) & (~drag_mask)

            active_mask = ~(self._static_mask[:n_elements] | self._sleep_mask[:n_elements])
            active_indices = np.where(active_mask)[0]
            
            # Cache window size for asymptote logic (M16/Baldor: simplify by caching)
            win_changed = not hasattr(self, '_prev_win_size') or self._prev_win_size != (win_w, win_h)
            self._prev_win_size = (win_w, win_h)
            
            # Select indices to process: if window changes, everyone needs a new target
            if win_changed:
                processing_indices = np.arange(n_elements)
            else:
                processing_indices = active_indices

            # 4. Target Calculation (Only for those moving or on window change)
            for idx in processing_indices:
                element = self._elements[idx]
                element.is_sleeping = False
                
                # Baldor's Principle: "Simplify the work by reusing known values"
                if win_changed or not hasattr(element, '_cached_target'):
                    target = element.calculate_asymptotes(win_w, win_h)
                    element._cached_target = target
                else:
                    target = element._cached_target

                if hasattr(element, '_override_asymptote'):
                    target = self.state_manager.lerp_arrays(target, element._override_asymptote, 0.1)
                self._batch_targets[idx] = target

            # 5. Handle targets for inactive ones (Snap to current state)
            if not win_changed:
                inactive_mask = ~active_mask[:n_elements]
                if inactive_mask.any():
                    self._batch_targets[:n_elements][inactive_mask] = states_view[inactive_mask]
                    # Update object attribute for external visibility
                    # Baldor: "Group similar terms to minimize operations"
                    # We ONLY update sleep status for non-static elements detected as sleeping
                    sleeping_indices = np.where(self._sleep_mask[:n_elements])[0]
                    for idx in sleeping_indices:
                        self._elements[idx].is_sleeping = True
            
            # Aether-Guard: Vectorized NaN/Inf sanitization (preserves 100% precision)
            # Valid elements remain unchanged; invalid elements get reset to zeros
            nan_mask_state = np.isnan(states_view) | np.isinf(states_view)
            nan_mask_vel = np.isnan(velocities_view) | np.isinf(velocities_view)
            
            if nan_mask_state.any():
                states_view[nan_mask_state] = np.float32(0.0)
            if nan_mask_vel.any():
                velocities_view[nan_mask_vel] = np.float32(0.0)

            # Check if all ACTIVE elements use the same stiffness
            uniform_stiffness = True
            stiffness = self._default_stiffness
            active_indices = np.where(active_mask)[0]
            for idx in active_indices:
                element = self._elements[idx]
                # Default to _default_stiffness if not set
                s = getattr(element, '_stiffness', self._default_stiffness)
                if s != stiffness:
                    uniform_stiffness = False
                    break

            if uniform_stiffness:
                # Fast path: single parallel kernel for all restoring forces
                solver.batch_restoring_forces(
                    self._batch_states, self._batch_targets,
                    float(stiffness), self._batch_forces
                )
            else:
                # Slow path: per-element stiffness
                for idx in active_indices:
                    element = self._elements[idx]
                    s = getattr(element, '_stiffness', self._default_stiffness)
                    cast(np.ndarray, self._batch_forces)[idx] = solver.calculate_restoring_force(
                        cast(np.ndarray, self._batch_states)[idx], 
                        cast(np.ndarray, self._batch_targets)[idx], 
                        float(s)
                    )

            # Add boundary forces (parallel batch)
            boundary_forces = np.zeros_like(self._batch_forces)
            solver.batch_boundary_forces(
                self._batch_states, float(win_w), float(win_h), 0.5, boundary_forces
            )
            self._batch_forces += boundary_forces
            
            # M16: Aplicar Máscara Booleana (Anular Fuerzas en Dormidos)
            inactive_mask = ~active_mask
            if inactive_mask.any():
                self._batch_forces[inactive_mask] = 0.0
                self._batch_velocities[inactive_mask] = 0.0

            # Handle drag override
            if self.input_manager.is_dragging and self.input_manager.dragged_element_index is not None:
                idx = self.input_manager.dragged_element_index
                if 0 <= idx < n_elements:
                    rect = self._batch_states[idx]
                    drag_force = self.input_manager.calculate_drag_force(
                        float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])
                    )
                    self._batch_forces[idx] = drag_force

            # Parallel integration
            solver.batch_integrate(
                self._batch_states, self._batch_velocities, self._batch_forces,
                max(self._dt, 0.001), active_viscosity, 5000.0
            )

            # Write back ONLY ACTIVE (Massive optimization for M16)
            for i in active_indices:
                elem = self._elements[i]
                elem.tensor.state[:] = self._batch_states[i]
                elem.tensor.velocity[:] = self._batch_velocities[i]
        else:
            # Original per-element loop (for small element counts or WASM)
            for idx, element in enumerate(self._elements):
                if hasattr(element, 'is_static'):
                    if element.is_static:
                        element.tensor.velocity[:] = 0.0
                        continue
                        
                    # WAKE UP if there is pending acceleration or drag
                    pending_accel = np.any(element.tensor.acceleration != 0)
                    is_dragged = (self.input_manager.is_dragging and self.input_manager.dragged_element_index == idx)
                    
                    if pending_accel or is_dragged:
                        element.is_sleeping = False

                    if element.is_sleeping:
                        vel_mag = np.linalg.norm(element.tensor.velocity)
                        # Solo puede seguir durmiendo si no hay aceleración
                        if vel_mag < element.sleep_epsilon and not pending_accel:
                            element.tensor.velocity[:] = 0.0
                            continue
                        else:
                            element.is_sleeping = False
                    else:
                        vel_mag = np.linalg.norm(element.tensor.velocity)
                        # Solo entra en sleep si vel < eps Y NO hay aceleración pendiente Y NO es arrastrado
                        if vel_mag < element.sleep_epsilon and not pending_accel and not is_dragged:
                            element.is_sleeping = True
                            element.tensor.velocity[:] = 0.0
                            continue

                target = element.calculate_asymptotes(win_w, win_h)

                if hasattr(element, '_override_asymptote'):
                    target = self.state_manager.lerp_arrays(target, element._override_asymptote, 0.1)

                stiffness = self._default_stiffness
                element_viscosity = active_viscosity

                if self._physics_coefficients is not None and idx < len(self._physics_coefficients):
                    coeff = self._physics_coefficients[idx]
                    stiffness = float(coeff['stiffness'])
                    element_viscosity = min(float(coeff['viscosity']) * viscosity_multiplier, 1.0)

                if hasattr(element, '_stiffness'):
                    stiffness = element._stiffness
                if hasattr(element, '_viscosity'):
                    element_viscosity = min(element._viscosity * viscosity_multiplier, 1.0)

                if self.input_manager.is_dragging and self.input_manager.dragged_element_index == idx:
                    rect = element.tensor.state
                    drag_force = self.input_manager.calculate_drag_force(
                        float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])
                    )
                    force = drag_force
                    element_viscosity = min(element_viscosity + InputManager.DRAG_DAMPING, 1.0)
                else:
                    force = solver.calculate_restoring_force(element.tensor.state, target, spring_constant=stiffness)

                force += solver.calculate_boundary_forces(element.tensor.state, win_w, win_h, boundary_stiffness=0.5)

                element.tensor.apply_force(force)
                element.tensor.euler_integrate(self._dt, viscosity=element_viscosity, target_state=target)
            
        # Data Extraction (zero-allocation: use direct properties instead of rendering_data dict)
        n_elements = len(self._elements)
        if n_elements == 0:
            return np.zeros(0, dtype=[('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')])
            
        data = np.zeros(n_elements, dtype=[('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')])
        for i, element in enumerate(self._elements):
            data[i]['rect'] = element.rect
            data[i]['color'] = element.color
            data[i]['z'] = element.z_index

        # HPC throttle: sleep if tick finished early to maintain 60-70% CPU
        # Only activate for heavy workloads (50+ elements) to avoid overhead on small demos
        if n_elements >= 50:
            _hpc_throttle(tick_start, time.perf_counter())

        return data
    
    @property
    def dt(self) -> float:
        return self._dt
    
    @property
    def element_count(self) -> int:
        return len(self._elements)
    
    def get_all_elements(self) -> list:
        """Return all registered elements.
        
        Returns:
            List of DifferentialElement objects currently in the engine.
        """
        return self._elements.copy()
    
    def get_ui_metadata(self) -> str:
        """Return JSON string containing metadata for elements that expose it.
        
        The Structured NumPy Array only holds floats, so non-physics data (strings,
        font sizes, component-specific metadata) must be exposed through a separate
        JSON bridge. This method collects all elements with a non-None metadata
        property and returns their data keyed by z-index.
        
        Returns:
            JSON string: {"z_index": {"type": "...", "text": "...", ...}}
        """
        metadata = {}
        for element in self._elements:
            meta = element.metadata
            if meta is not None:
                z_key = str(element._z_index)
                metadata[z_key] = meta
        return to_json(metadata)
    
    def _apply_genre_orbit(self, genre_idx: int, stiffness: float,
                           center_x: float, center_y: float) -> None:
        """
        Apply Hooke's Law attraction toward center for elements matching the focused genre.
        
        Args:
            genre_idx: Index into genre_vector (0=Action, 1=SciFi, 2=Drama, 3=Comedy)
            stiffness: Spring constant for orbit attraction
            center_x: X coordinate of orbit center
            center_y: Y coordinate of orbit center
        """
        for element in self._elements:
            if not hasattr(element, '_odyssey_metadata'):
                continue
            
            meta = element._odyssey_metadata
            gv = meta.get('genre_vector', [0.25, 0.25, 0.25, 0.25])
            match_strength = gv[genre_idx] if genre_idx < len(gv) else 0.0
            
            if match_strength > 0.3:
                rect = element.tensor.state
                cx = float(rect[0]) + float(rect[2]) / 2.0
                cy = float(rect[1]) + float(rect[3]) / 2.0
                
                dx = center_x - cx
                dy = center_y - cy
                
                force_x = dx * stiffness * match_strength
                force_y = dy * stiffness * match_strength
                
                element.tensor.apply_force(
                    np.array([force_x, force_y, 0.0, 0.0], dtype=np.float32)
                )
    
    def _trigger_supernova(self, center_x: float, center_y: float) -> None:
        """
        Apply a massive radial explosion force to all elements.
        Aether-Guard will clamp the forces to safe levels.
        
        Args:
            center_x: X coordinate of supernova center
            center_y: Y coordinate of supernova center
        """
        for element in self._elements:
            rect = element.tensor.state
            cx = float(rect[0]) + float(rect[2]) / 2.0
            cy = float(rect[1]) + float(rect[3]) / 2.0
            
            dx = cx - center_x
            dy = cy - center_y
            dist = max(1.0, np.sqrt(dx * dx + dy * dy))
            
            force_x = (dx / dist) * SUPERNOVA_FORCE
            force_y = (dy / dist) * SUPERNOVA_FORCE
            
            element.tensor.apply_force(
                np.array([force_x, force_y, 0.0, 0.0], dtype=np.float32)
            )
