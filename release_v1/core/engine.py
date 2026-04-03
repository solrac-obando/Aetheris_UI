import time
import json
import numpy as np
from typing import List, Optional
from core.aether_math import StateTensor
from core.elements import DifferentialElement, CanvasTextNode, DOMTextNode
from core import solver_bridge as solver
from core.state_manager import StateManager
from core.tensor_compiler import TensorCompiler
from core.input_manager import InputManager


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
        current_time = time.perf_counter()
        self._dt = current_time - self._last_time
        self._last_time = current_time
        
        # Phase 10: Check for layout shock (Window teleportation)
        viscosity_multiplier = self.state_manager.check_teleportation_shock(win_w, win_h)
        base_viscosity = self._default_viscosity
        active_viscosity = min(base_viscosity * viscosity_multiplier, 1.0)
        
        # Process physics
        for idx, element in enumerate(self._elements):
            target = element.calculate_asymptotes(win_w, win_h)
            
            # Override target if transitioning
            if hasattr(element, '_override_asymptote'):
                target = self.state_manager.lerp_arrays(target, element._override_asymptote, 0.1)
            
            # Phase 11: Get element-specific physics coefficients
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
            
            # Phase 19: Input handling - drag force overrides restoring force
            if self.input_manager.is_dragging and self.input_manager.dragged_element_index == idx:
                # Apply drag force instead of restoring force
                rect = element.tensor.state
                drag_force = self.input_manager.calculate_drag_force(
                    float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])
                )
                force = drag_force
                # Use extra damping during drag for stability
                element_viscosity = min(element_viscosity + InputManager.DRAG_DAMPING, 1.0)
            else:
                # Normal physics: restoring force + boundary forces
                force = solver.calculate_restoring_force(element.tensor.state, target, spring_constant=stiffness)
            
            force += solver.calculate_boundary_forces(element.tensor.state, win_w, win_h, boundary_stiffness=0.5)
            
            element.tensor.apply_force(force)
            
            # Phase 9.5 integration: pass the target for Epsilon Snapping
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
