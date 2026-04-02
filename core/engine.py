import time
import numpy as np
from typing import List
from core.aether_math import StateTensor
from core.elements import DifferentialElement
from core import solver


class AetherEngine:
    """The heart of Aetheris UI - responsible for the temporal pulse of the application.
    
    This orchestrator synchronizes physics simulation, intelligent asymptote calculation,
    and prepares data for GPU rendering in a high-performance pipeline.
    """
    
    def __init__(self):
        """Initialize the engine with an empty registry and time tracking."""
        self._elements: List[DifferentialElement] = []
        self._last_time = time.perf_counter()
        self._dt = 0.0
    
    def register_element(self, element: DifferentialElement) -> None:
        """Register a differential element with the engine.
        
        Args:
            element: The element to register for physics simulation
        """
        self._elements.append(element)
    
    def tick(self, win_w: float, win_h: float) -> np.ndarray:
        """Execute one frame of the engine's temporal pulse.
        
        This is the core loop that:
        1. Calculates precise delta time using temporal variation principles
        2. Synchronizes asymptotes for all elements based on container size
        3. Computes forces using Hooke's law and boundary constraints
        4. Applies forces and integrates physics state
        5. Extracts and returns structured data for GPU rendering
        
        Args:
            win_w: Current window width in pixels
            win_h: Current window height in pixels
            
        Returns:
            numpy.ndarray: Structured array with dtype [('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')]
        """
        # Calculate delta time using functional variation (temporal derivative)
        current_time = time.perf_counter()
        self._dt = current_time - self._last_time
        self._last_time = current_time
        
        # Process each element in the registry
        for element in self._elements:
            # 1. Sync asymptotes: Calculate target state based on container size
            target_state = element.calculate_asymptotes(win_w, win_h)
            
            # 2. Compute forces using our solver
            # Restoring force (Hooke's law): pulls element toward its target
            restoring_force = solver.calculate_restoring_force(
                element.tensor.state, target_state, spring_constant=0.1
            )
            
            # Boundary force: keeps element within window bounds
            boundary_force = solver.calculate_boundary_forces(
                element.tensor.state, win_w, win_h, boundary_stiffness=0.5
            )
            
            # 3. Apply & Integrate: Combine forces and update physics
            total_force = restoring_force + boundary_force
            element.tensor.apply_force(total_force)
            element.tensor.euler_integrate(self._dt, viscosity=0.1)
        
        # 4. Data Extraction: Prepare flat structured array for GPU
        # Pre-allocate array for performance
        n_elements = len(self._elements)
        if n_elements == 0:
            # Return empty array with correct dtype
            return np.zeros(0, dtype=[('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')])
        
        # Create structured array
        data = np.zeros(n_elements, dtype=[('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')])
        
        # Fill data efficiently
        for i, element in enumerate(self._elements):
            rendering_data = element.rendering_data
            data[i]['rect'] = rendering_data['rect']
            data[i]['color'] = rendering_data['color']
            data[i]['z'] = rendering_data['z']
        
        return data
    
    @property
    def dt(self) -> float:
        """Get the delta time of the last frame."""
        return self._dt
    
    @property
    def element_count(self) -> int:
        """Get the number of registered elements."""
        return len(self._elements)