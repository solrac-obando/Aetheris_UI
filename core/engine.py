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
from core.tensor_compiler import TensorCompiler
from core.input_manager import InputManager


# ── HPC Resource Throttle: Target 60-70% CPU utilization ──────────────────
_HPC_TARGET_FRAME_MS = 16.667  # 60 FPS budget
_HPC_CPU_TARGET = 0.60         # 60% of available cores
_HPC_THROTTLE_ENABLED = True   # Set False to disable throttle (tests set this to False)


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
        self._elements.append(element)
        
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

            # Compute targets for all elements (Python loop — unavoidable for asymptote calculation)
            for idx, element in enumerate(self._elements):
                target = element.calculate_asymptotes(win_w, win_h)
                if hasattr(element, '_override_asymptote'):
                    target = self.state_manager.lerp_arrays(target, element._override_asymptote, 0.1)
                self._batch_targets[idx] = target

            # Sync state/velocity to batch (minimized: direct numpy assignment)
            for i, elem in enumerate(self._elements):
                # Aether-Guard: sanitize NaN/Inf during copy
                for j in range(4):
                    sv = float(elem.tensor.state[j])
                    if np.isnan(sv) or np.isinf(sv):
                        elem.tensor.state[j] = np.float32(0.0)
                    vv = float(elem.tensor.velocity[j])
                    if np.isnan(vv) or np.isinf(vv):
                        elem.tensor.velocity[j] = np.float32(0.0)
                self._batch_states[i] = elem.tensor.state
                self._batch_velocities[i] = elem.tensor.velocity

            # Check if all elements use the same stiffness (fast path)
            uniform_stiffness = True
            stiffness = self._default_stiffness
            for idx, element in enumerate(self._elements):
                s = self._default_stiffness
                if hasattr(element, '_stiffness'):
                    s = element._stiffness
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
                for idx, element in enumerate(self._elements):
                    s = self._default_stiffness
                    if hasattr(element, '_stiffness'):
                        s = element._stiffness
                    self._batch_forces[idx] = solver.calculate_restoring_force(
                        self._batch_states[idx], self._batch_targets[idx], float(s)
                    )

            # Add boundary forces (parallel batch)
            boundary_forces = np.zeros_like(self._batch_forces)
            solver.batch_boundary_forces(
                self._batch_states, float(win_w), float(win_h), 0.5, boundary_forces
            )
            self._batch_forces += boundary_forces

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

            # Write back (minimized: direct numpy copy)
            for i, elem in enumerate(self._elements):
                elem.tensor.state[:] = self._batch_states[i]
                elem.tensor.velocity[:] = self._batch_velocities[i]
        else:
            # Original per-element loop (for small element counts or WASM)
            for idx, element in enumerate(self._elements):
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
            
        # Data Extraction
        n_elements = len(self._elements)
        if n_elements == 0:
            return np.zeros(0, dtype=[('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')])
            
        data = np.zeros(n_elements, dtype=[('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')])
        for i, element in enumerate(self._elements):
            r_data = element.rendering_data
            data[i]['rect'] = r_data['rect']
            data[i]['color'] = r_data['color']
            data[i]['z'] = r_data['z']

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
    
    def get_ui_metadata(self) -> str:
        """Return JSON string containing text metadata for CanvasTextNode and DOMTextNode elements.
        
        The Structured NumPy Array only holds floats, so text data (strings, font sizes)
        must be exposed through a separate JSON bridge. This method collects all
        text-based elements and returns their metadata keyed by z-index.
        
        Returns:
            JSON string: {"z_index": {"type": "canvas_text|dom_text", "text": "...", ...}}
        """
        metadata = {}
        for element in self._elements:
            if isinstance(element, (CanvasTextNode, DOMTextNode)):
                z_key = str(element._z_index)
                metadata[z_key] = element.text_metadata
        return json.dumps(metadata)
    
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
