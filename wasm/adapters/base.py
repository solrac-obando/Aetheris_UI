# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Base adapter interfaces for WASM rendering backends.

Defines the abstract interface (AdapterInterface) that all renderers must implement,
ensuring backwards compatibility with the existing WebBridge API.
"""
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple


class AdapterType(Enum):
    """Types of rendering adapters supported."""
    JS_RENDERER = auto()
    PYODIDE = auto()
    WEBGL = auto()
    REST = auto()


class RendererCapability(Enum):
    """Capability flags for renderer detection."""
    CANVAS_2D = auto()
    WEBGL = auto()
    WEBGL2_COMPUTE = auto()
    WEBASM = auto()
    WORKER_THREADS = auto()


class AdapterInterface(ABC):
    """
    Abstract base class for all rendering adapters.
    
    All adapters must implement this interface to ensure API compatibility
    with the existing WebBridge class. The same public methods and signatures
    must be maintained for backwards compatibility.
    """

    @abstractmethod
    def sync(self, elements: List[Any]) -> str:
        """
        Generate a JSON payload of current element positions for the web client.
        
        Args:
            elements: List of DifferentialElement objects from AetherEngine.
            
        Returns:
            JSON string: {"frame": N, "elements": [{"id": "...", "x": 0, "y": 0, "w": 0, "h": 0}, ...]}
        """
        pass

    @abstractmethod
    def register_element(self, index: int, html_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Register an element from the engine with a corresponding HTML ID.
        
        Args:
            index: Internal element index from AetherEngine.
            html_id: Corresponding HTML element ID.
            metadata: Optional metadata dict (tag, classes, text, styles).
        """
        pass

    @abstractmethod
    def unregister_element(self, index: int) -> None:
        """
        Remove an element from the adapter.
        
        Args:
            index: Internal element index to remove.
        """
        pass

    @abstractmethod
    def get_initial_dom_state(self) -> List[Dict[str, Any]]:
        """
        Generate the initial HTML structure needed to render all elements.
        
        Returns:
            List of dicts with HTML creation instructions.
        """
        pass

    @property
    @abstractmethod
    def element_count(self) -> int:
        """Return the number of registered elements."""
        pass

    @property
    @abstractmethod
    def stats(self) -> Dict[str, Any]:
        """Return adapter statistics (frames, sync time, etc.)."""
        pass

    @property
    @abstractmethod
    def adapter_type(self) -> AdapterType:
        """Return the type of this adapter."""
        pass

    @property
    @abstractmethod
    def bundle_size(self) -> int:
        """Return the estimated bundle size in bytes."""
        pass


class CapabilityDetector:
    """Detects browser capabilities to select the best adapter."""
    
    @staticmethod
    def detect(capabilities: List[RendererCapability]) -> List[RendererCapability]:
        """
        Detect which capabilities are available in the current environment.
        
        Args:
            capabilities: List of capabilities to check.
            
        Returns:
            List of available capabilities.
        """
        available = []
        
        for cap in capabilities:
            if cap == RendererCapability.CANVAS_2D:
                available.append(cap)
            elif cap == RendererCapability.WEBGL:
                available.append(cap)
            elif cap == RendererCapability.WEBGL2_COMPUTE:
                available.append(cap)
            elif cap == RendererCapability.WEBASM:
                available.append(cap)
            elif cap == RendererCapability.WORKER_THREADS:
                available.append(cap)
                
        return available
    
    @staticmethod
    def select_adapter(capabilities: List[RendererCapability]) -> AdapterType:
        """
        Select the best adapter based on available capabilities.
        
        Args:
            capabilities: List of detected capabilities.
            
        Returns:
            Recommended AdapterType.
        """
        if RendererCapability.WEBGL2_COMPUTE in capabilities:
            return AdapterType.WEBGL
        elif RendererCapability.WEBGL in capabilities:
            return AdapterType.WEBGL
        elif RendererCapability.CANVAS_2D in capabilities:
            return AdapterType.JS_RENDERER
        else:
            return AdapterType.PYODIDE