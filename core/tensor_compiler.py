# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Tensor Compiler with dual-path execution for WASM/Pyodide compatibility.
Falls back to pure NumPy when Numba is unavailable.
"""
import numpy as np

try:
    from numba import njit
    HAS_NUMBA = True
except (ImportError, ModuleNotFoundError):
    HAS_NUMBA = False


if HAS_NUMBA:
    @njit(cache=True)
    def _speed_to_stiffness(transition_time_ms: float) -> float:
        if transition_time_ms <= 0.0:
            return 0.1
        T_sec = transition_time_ms / 1000.0
        if T_sec < 0.001:
            T_sec = 0.001
        k = 16.0 / (T_sec * T_sec)
        return np.float32(min(k, 10000.0))

    @njit(cache=True)
    def _speed_to_viscosity(transition_time_ms: float) -> float:
        if transition_time_ms <= 0.0:
            return 0.1
        viscosity = 1.0 - (transition_time_ms / 1000.0)
        return np.float32(max(0.05, min(viscosity, 0.95)))
else:
    def _speed_to_stiffness(transition_time_ms: float) -> float:
        if transition_time_ms <= 0.0:
            return 0.1
        T_sec = transition_time_ms / 1000.0
        if T_sec < 0.001:
            T_sec = 0.001
        k = 16.0 / (T_sec * T_sec)
        return np.float32(min(k, 10000.0))

    def _speed_to_viscosity(transition_time_ms: float) -> float:
        if transition_time_ms <= 0.0:
            return 0.1
        viscosity = 1.0 - (transition_time_ms / 1000.0)
        return np.float32(max(0.05, min(viscosity, 0.95)))


class TensorCompiler:
    """Compiles Design Tokens (JSON) into Physics Coefficients (NumPy)."""
    
    STIFFNESS_MAP = {
        "snappy": 0.8,
        "organic": 0.1,
        "fluid": 0.05,
        "rigid": 2.0,
        "gentle": 0.02,
    }
    
    VISCOSITY_MAP = {
        "snappy": 0.3,
        "organic": 0.5,
        "fluid": 0.7,
        "rigid": 0.1,
        "gentle": 0.85,
    }
    
    def compile_intent(self, intent_json: dict) -> np.ndarray:
        layout = intent_json.get("layout", "column")
        spacing = float(intent_json.get("spacing", 0))
        animation_raw = intent_json.get("animation", "organic")
        if isinstance(animation_raw, dict):
            animation = animation_raw.get("style", "organic")
        else:
            animation = str(animation_raw)
            
        transition_speed_ms = float(intent_json.get("transition_speed_ms", 300))
        
        raw_padding = intent_json.get("padding", 0)
        if isinstance(raw_padding, (int, float)):
            padding = [float(raw_padding)] * 4
        elif isinstance(raw_padding, (list, tuple)):
            if len(raw_padding) == 1:
                padding = [float(raw_padding[0])] * 4
            elif len(raw_padding) == 2:
                padding = [float(raw_padding[0]), float(raw_padding[1]),
                          float(raw_padding[0]), float(raw_padding[1])]
            elif len(raw_padding) == 4:
                padding = [float(p) for p in raw_padding]
            else:
                padding = [0.0] * 4
        else:
            padding = [0.0] * 4
        
        base_stiffness = self.STIFFNESS_MAP.get(animation, 0.1)
        base_viscosity = self.VISCOSITY_MAP.get(animation, 0.5)
        
        if "transition_speed_ms" in intent_json:
            derived_k = _speed_to_stiffness(transition_speed_ms)
            derived_viscosity = _speed_to_viscosity(transition_speed_ms)
            base_stiffness = 0.7 * derived_k + 0.3 * base_stiffness
            base_viscosity = 0.7 * derived_viscosity + 0.3 * base_viscosity
        
        elements = intent_json.get("elements", [])
        n_elements = max(len(elements), 1)
        
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
            elem_animation = elem.get("animation", animation)
            elem_stiffness = self.STIFFNESS_MAP.get(elem_animation, base_stiffness)
            elem_viscosity = self.VISCOSITY_MAP.get(elem_animation, base_viscosity)
            
            if "stiffness" in elem:
                elem_stiffness = float(elem["stiffness"])
            if "viscosity" in elem:
                elem_viscosity = float(elem["viscosity"])
            
            coefficients[i]['stiffness'] = np.float32(elem_stiffness)
            coefficients[i]['viscosity'] = np.float32(elem_viscosity)
            coefficients[i]['boundary_padding'] = np.array(padding, dtype=np.float32)
            coefficients[i]['spacing'] = np.float32(spacing)
        
        if len(elements) == 0:
            coefficients[0]['element_id'] = "default"
            coefficients[0]['stiffness'] = np.float32(base_stiffness)
            coefficients[0]['viscosity'] = np.float32(base_viscosity)
            coefficients[0]['boundary_padding'] = np.array(padding, dtype=np.float32)
            coefficients[0]['spacing'] = np.float32(spacing)
        
        return coefficients
    
    def apply_coefficients(self, engine, coefficients: np.ndarray) -> None:
        engine._physics_coefficients = coefficients.copy()
        
        if hasattr(engine, '_elements'):
            for elem_coeff in coefficients:
                elem_id = str(elem_coeff['element_id'])
                for element in engine._elements:
                    if hasattr(element, '_id') and element._id == elem_id:
                        element._stiffness = float(elem_coeff['stiffness'])
                        element._viscosity = float(elem_coeff['viscosity'])
                        element._boundary_padding = elem_coeff['boundary_padding'].copy()
                        element._spacing = float(elem_coeff['spacing'])
    
    def get_default_coefficients(self, animation: str = "organic", 
                                  spacing: float = 0.0,
                                  padding: float = 0.0) -> np.ndarray:
        return self.compile_intent({
            "animation": animation,
            "spacing": spacing,
            "padding": padding,
        })
