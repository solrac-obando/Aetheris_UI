# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Object Pooling System for Aetheris.

Reduces Garbage Collection pressure by recycling DifferentialElement instances.
Crucial for high-performance WASM/Web deployments where memory allocation
is expensive.
"""
from typing import Dict, List, Type, Any, Tuple, Optional
from core.elements import DifferentialElement


class ElementPool:
    """Manages pools of DifferentialElement subclasses for reuse.
    
    Example:
        pool = ElementPool()
        box = pool.acquire(StaticBox, x=10, y=10, w=100, h=100)
        # ... use box ...
        pool.release(box)
    """
    
    def __init__(self) -> None:
        self._pools: Dict[Type[DifferentialElement], List[DifferentialElement]] = {}

    def acquire(self, element_class: Type[DifferentialElement], 
                x: float, y: float, w: float, h: float, 
                color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0), 
                z: int = 0) -> DifferentialElement:
        """Get an element from the pool or create a new one if empty.
        
        Args:
            element_class: Subclass of DifferentialElement to acquire
            x, y, w, h: Physics parameters
            color: RGBA tuple
            z: Z-index
            
        Returns:
            DifferentialElement: A ready-to-use element instance.
        """
        if element_class not in self._pools:
            self._pools[element_class] = []
            
        pool = self._pools[element_class]
        
        if pool:
            element = pool.pop()
            element.reset(x, y, w, h, color, z)
            return element
        else:
            return element_class(x, y, w, h, color, z)

    def release(self, element: DifferentialElement) -> None:
        """Return an element to its respective pool for future reuse.
        
        Args:
            element: The element instance to recycle.
        """
        element_class = type(element)
        if element_class not in self._pools:
            self._pools[element_class] = []
            
        # Clean up element state before pooling
        # We don't call dispose() because we want to reuse the internal buffers
        element._disposed = True  # Mark as "inactive" while in pool
        self._pools[element_class].append(element)

    def prewarm(self, element_class: Type[DifferentialElement], count: int) -> None:
        """Populate a pool with a specific number of instances in advance.
        
        Useful during application loading to avoid stutter during runtime.
        """
        if element_class not in self._pools:
            self._pools[element_class] = []
            
        pool = self._pools[element_class]
        for _ in range(count):
            # Create with default params, will be reset on acquire
            element = element_class(0, 0, 1, 1)
            element._disposed = True
            pool.append(element)

    def clear(self) -> None:
        """Dispose all elements currently in pools and clear the pools."""
        for pool in self._pools.values():
            for element in pool:
                # Force disposal of pooled elements
                element._disposed = False # Unmark for dispose to work
                element.dispose()
        self._pools.clear()
