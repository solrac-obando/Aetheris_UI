import numpy as np
from numba import njit


@njit(cache=True)
def speed_to_stiffness(transition_time_ms: float) -> float:
    """
    Derive Spring Constant (k) from transition duration (T).
    
    Mathematical Derivation (from Precálculo - Sistemas Lineales):
    ---------------------------------------------------------------
    For a critically damped spring-mass system:
    - Critical damping: c = 2*sqrt(m*k)
    - With unit mass (m=1): c = 2*sqrt(k)
    - Time constant: tau = 2m/c = 2/(2*sqrt(k)) = 1/sqrt(k)
    - Settling time (4*tau): T_settle = 4*tau = 4/sqrt(k)
    
    Solving for k:
    T = 4/sqrt(k)  =>  sqrt(k) = 4/T  =>  k = 16/T^2
    
    Where T is in seconds. For milliseconds:
    k = 16 / (T_ms / 1000)^2 = 16 * 10^6 / T_ms^2
    
    Args:
        transition_time_ms: Desired transition duration in milliseconds
        
    Returns:
        Spring constant k for use in calculate_restoring_force
    """
    if transition_time_ms <= 0.0:
        return 0.1  # Default fallback
    
    T_sec = transition_time_ms / 1000.0
    if T_sec < 0.001:  # Prevent division by near-zero
        T_sec = 0.001
    
    k = 16.0 / (T_sec * T_sec)
    return np.float32(min(k, 10000.0))  # Cap to prevent numerical explosion


@njit(cache=True)
def speed_to_viscosity(transition_time_ms: float) -> float:
    """
    Derive optimal viscosity (damping ratio) from transition speed.
    
    For critical damping with m=1:
    - c_critical = 2*sqrt(k)
    - viscosity = c_critical / (2*sqrt(k)) = 1.0 for critical damping
    
    However, UI elements benefit from slight under-damping (0.7-0.9)
    for a more natural "bounce" feel.
    
    Faster transitions need higher viscosity to prevent overshoot.
    
    Args:
        transition_time_ms: Desired transition duration in milliseconds
        
    Returns:
        Viscosity value (0.0-1.0) for euler_integrate
    """
    if transition_time_ms <= 0.0:
        return 0.1
    
    # Map: fast (100ms) -> 0.9, medium (300ms) -> 0.5, slow (600ms) -> 0.2
    # Linear interpolation: viscosity = 1.0 - (T_ms / 1000)
    viscosity = 1.0 - (transition_time_ms / 1000.0)
    return np.float32(max(0.05, min(viscosity, 0.95)))


class TensorCompiler:
    """Compiles Design Tokens (JSON) into Physics Coefficients (NumPy).
    
    This is the 'Middle-end' of Aetheris UI - it bridges the gap between
    high-level design intent (JSON layout descriptions) and low-level
    physics execution (spring constants, viscosity, boundary offsets).
    
    Mathematical Foundation:
    - Uses linear system theory from Precálculo to map time->stiffness
    - Applies proportionality from Álgebra de Baldor for padding/margin scaling
    """
    
    STIFFNESS_MAP = {
        "snappy": 0.8,       # High k - fast, responsive
        "organic": 0.1,      # Medium k - natural feel
        "fluid": 0.05,       # Low k - smooth, flowing
        "rigid": 2.0,        # Very high k - almost instant
        "gentle": 0.02,      # Very low k - soft, dreamy
    }
    
    VISCOSITY_MAP = {
        "snappy": 0.3,
        "organic": 0.5,
        "fluid": 0.7,
        "rigid": 0.1,
        "gentle": 0.85,
    }
    
    def compile_intent(self, intent_json: dict) -> np.ndarray:
        """Compile a design intent JSON into a physics coefficient array.
        
        Args:
            intent_json: Dictionary containing:
                - layout: 'column', 'row', 'grid', etc.
                - spacing: pixel spacing between elements
                - padding: edge padding (can be single value or [top, right, bottom, left])
                - animation: 'snappy', 'organic', 'fluid', 'rigid', 'gentle'
                - transition_speed_ms: optional override for animation timing
                - elements: list of element definitions with individual overrides
                
        Returns:
            Structured numpy array with dtype:
            [('element_id', 'U64'), ('stiffness', 'f4'), ('viscosity', 'f4'),
             ('boundary_padding', 'f4', 4), ('spacing', 'f4')]
        """
        # Extract design parameters
        layout = intent_json.get("layout", "column")
        spacing = float(intent_json.get("spacing", 0))
        animation = intent_json.get("animation", "organic")
        transition_speed_ms = float(intent_json.get("transition_speed_ms", 300))
        
        # Parse padding (can be single value or 4-value array)
        raw_padding = intent_json.get("padding", 0)
        if isinstance(raw_padding, (int, float)):
            padding = [float(raw_padding)] * 4
        elif isinstance(raw_padding, (list, tuple)):
            if len(raw_padding) == 1:
                padding = [float(raw_padding[0])] * 4
            elif len(raw_padding) == 2:  # [vertical, horizontal]
                padding = [float(raw_padding[0]), float(raw_padding[1]),
                          float(raw_padding[0]), float(raw_padding[1])]
            elif len(raw_padding) == 4:  # [top, right, bottom, left]
                padding = [float(p) for p in raw_padding]
            else:
                padding = [0.0] * 4
        else:
            padding = [0.0] * 4
        
        # Get base physics coefficients from animation preset
        base_stiffness = self.STIFFNESS_MAP.get(animation, 0.1)
        base_viscosity = self.VISCOSITY_MAP.get(animation, 0.5)
        
        # If explicit transition_speed_ms is provided, derive k mathematically
        if "transition_speed_ms" in intent_json:
            derived_k = speed_to_stiffness(transition_speed_ms)
            derived_viscosity = speed_to_viscosity(transition_speed_ms)
            # Blend: 70% derived, 30% preset (smooth transition)
            base_stiffness = 0.7 * derived_k + 0.3 * base_stiffness
            base_viscosity = 0.7 * derived_viscosity + 0.3 * base_viscosity
        
        # Process individual elements
        elements = intent_json.get("elements", [])
        n_elements = max(len(elements), 1)
        
        # Create structured output array
        dtype = [
            ('element_id', 'U64'),
            ('stiffness', 'f4'),
            ('viscosity', 'f4'),
            ('boundary_padding', 'f4', 4),
            ('spacing', 'f4'),
        ]
        coefficients = np.zeros(n_elements, dtype=dtype)
        
        for i, elem in enumerate(elements):
            elem_id = elem.get("id", f"element_{i}")
            coefficients[i]['element_id'] = elem_id
            
            # Element-specific overrides
            elem_animation = elem.get("animation", animation)
            elem_stiffness = self.STIFFNESS_MAP.get(elem_animation, base_stiffness)
            elem_viscosity = self.VISCOSITY_MAP.get(elem_animation, base_viscosity)
            
            # Override with explicit values if provided
            if "stiffness" in elem:
                elem_stiffness = float(elem["stiffness"])
            if "viscosity" in elem:
                elem_viscosity = float(elem["viscosity"])
            
            coefficients[i]['stiffness'] = np.float32(elem_stiffness)
            coefficients[i]['viscosity'] = np.float32(elem_viscosity)
            coefficients[i]['boundary_padding'] = np.array(padding, dtype=np.float32)
            coefficients[i]['spacing'] = np.float32(spacing)
        
        # If no elements defined, create a default entry
        if len(elements) == 0:
            coefficients[0]['element_id'] = "default"
            coefficients[0]['stiffness'] = np.float32(base_stiffness)
            coefficients[0]['viscosity'] = np.float32(base_viscosity)
            coefficients[0]['boundary_padding'] = np.array(padding, dtype=np.float32)
            coefficients[0]['spacing'] = np.float32(spacing)
        
        return coefficients
    
    def apply_coefficients(self, engine, coefficients: np.ndarray) -> None:
        """Apply compiled physics coefficients to an AetherEngine instance.
        
        This updates the engine's physics parameters in real-time without
        requiring element re-instantiation.
        
        Args:
            engine: AetherEngine instance to update
            coefficients: Structured array from compile_intent()
        """
        # Store coefficients in engine for use during tick()
        engine._physics_coefficients = coefficients.copy()
        
        # Apply to elements that have matching IDs
        if hasattr(engine, '_elements'):
            for elem_coeff in coefficients:
                elem_id = str(elem_coeff['element_id'])
                
                # Find matching element by checking if it has this ID
                for element in engine._elements:
                    # Check if element has an ID attribute matching
                    if hasattr(element, '_id') and element._id == elem_id:
                        element._stiffness = float(elem_coeff['stiffness'])
                        element._viscosity = float(elem_coeff['viscosity'])
                        element._boundary_padding = elem_coeff['boundary_padding'].copy()
                        element._spacing = float(elem_coeff['spacing'])
    
    def get_default_coefficients(self, animation: str = "organic", 
                                  spacing: float = 0.0,
                                  padding: float = 0.0) -> np.ndarray:
        """Get default physics coefficients for a given animation style.
        
        Args:
            animation: Animation preset name
            spacing: Default spacing between elements
            padding: Default boundary padding
            
        Returns:
            Single-element structured array with default coefficients
        """
        return self.compile_intent({
            "animation": animation,
            "spacing": spacing,
            "padding": padding,
        })