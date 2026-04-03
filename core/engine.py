import time
import json
import numpy as np
from typing import List, Optional
from core.aether_math import StateTensor
from core.elements import DifferentialElement, CanvasTextNode, DOMTextNode
from core import solver_bridge as solver
from core.state_manager import StateManager
from core.tensor_compiler import TensorCompiler


class AetherEngine:
    def __init__(self):
        self._elements: List[DifferentialElement] = []
        self._last_time = time.perf_counter()
        self._dt = 0.0
        self.state_manager = StateManager()
        self.tensor_compiler = TensorCompiler()
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
            
            # Solver with dynamic stiffness (dual-path: Numba or Pure NumPy)
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
