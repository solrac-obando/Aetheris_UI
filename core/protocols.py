# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Protocols for Aetheris UI components.
Provides structural typing (duck typing) for engines and other core parts.
"""
from typing import Protocol, runtime_checkable, Any, Dict, Optional
import numpy as np

@runtime_checkable
class AetherEngineProtocol(Protocol):
    """Structural interface that any Aetheris physics engine must implement."""
    
    @property
    def element_count(self) -> int: ...
    
    @property
    def dt(self) -> float: ...
    
    @property
    def state_manager(self) -> Any: ...
    
    @property
    def input_manager(self) -> Any: ...
    
    @property
    def tensor_compiler(self) -> Any: ...
    
    def register_element(self, element: Any) -> None: ...
    
    def handle_pointer_down(self, x: float, y: float) -> None: ...
    
    def handle_pointer_move(self, x: float, y: float) -> None: ...
    
    def handle_pointer_up(self) -> None: ...
    
    def tick(self, win_w: float, win_h: float) -> np.ndarray: ...
    
    def get_ui_metadata(self) -> str: ...
