# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
PyodideFallback: Backwards-compatible wrapper for Pyodide.

This module wraps the existing Pyodide integration to ensure backwards
compatibility when the light WASM adapter fails or is not available.
"""
import json
import time
from typing import Any, Dict, List, Optional

from wasm.adapters.base import AdapterInterface, AdapterType

_BUNDLE_SIZE_PYODIDE = 40 * 1024 * 1024


class PyodideFallback(AdapterInterface):
    """
    Fallback adapter that uses Pyodide for rendering.
    
    This adapter maintains full compatibility with the original
    WebBridge implementation and is used when JSRenderer fails.
    """

    def __init__(
        self,
        container_width: float = 1280.0,
        container_height: float = 720.0,
    ):
        self._container_w = container_width
        self._container_h = container_height
        self._element_map: Dict[int, str] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._last_sync_time = 0.0
        self._sync_count = 0
        self._pyodide_loaded = False

    @property
    def element_count(self) -> int:
        return len(self._element_map)

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "elements": self.element_count,
            "sync_frames": self._sync_count,
            "last_sync": self._last_sync_time,
            "pyodide_loaded": self._pyodide_loaded,
        }

    @property
    def adapter_type(self) -> AdapterType:
        return AdapterType.PYODIDE

    @property
    def bundle_size(self) -> int:
        return _BUNDLE_SIZE_PYODIDE

    def detect_capabilities(self) -> Dict[str, bool]:
        return {
            "canvas_2d": True,
            "webgl": True,
            "pyodide": self._pyodide_loaded,
            "wasm": True,
        }

    def sync(
        self,
        elements: List[Any],
        element_map: Optional[Dict[int, str]] = None,
        metadata: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> str:
        """
        Generate JSON payload using Pyodide-compatible format.
        
        This method produces the same output format as the original
        WebBridge to ensure complete backwards compatibility.
        """
        self._sync_count += 1
        self._last_sync_time = time.perf_counter()

        if element_map is None:
            element_map = self._element_map
        if metadata is None:
            metadata = self._metadata

        payload = {
            "frame": self._sync_count,
            "timestamp": self._last_sync_time,
            "elements": [],
        }

        for idx, elem in enumerate(elements):
            html_id = element_map.get(idx)
            if not html_id:
                continue

            try:
                state = elem.tensor.state
                x, y, w, h = (
                    float(state[0]),
                    float(state[1]),
                    float(state[2]),
                    float(state[3]),
                )
            except AttributeError:
                continue

            if not (self._is_finite(x) and self._is_finite(y) and self._is_finite(w) and self._is_finite(h)):
                continue

            x = max(0.0, min(x, self._container_w - w))
            y = max(0.0, min(y, self._container_h - h))

            payload["elements"].append({
                "id": html_id,
                "x": round(x, 2),
                "y": round(y, 2),
                "w": round(w, 2),
                "h": round(h, 2),
                "z": getattr(elem, "_z_index", idx),
            })

        return json.dumps(payload)

    def _is_finite(self, value: float) -> bool:
        import math
        return math.isfinite(value)

    def register_element(
        self,
        index: int,
        html_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._element_map[index] = html_id
        if metadata:
            self._metadata[html_id] = metadata
        else:
            self._metadata[html_id] = {"tag": "div", "classes": [], "text": ""}

    def unregister_element(self, index: int) -> None:
        html_id = self._element_map.pop(index, None)
        if html_id:
            self._metadata.pop(html_id, None)

    def get_initial_dom_state(self) -> List[Dict[str, Any]]:
        dom_elements = []
        for idx, html_id in self._element_map.items():
            meta = self._metadata.get(html_id, {})
            dom_elements.append({
                "id": html_id,
                "tag": meta.get("tag", "div"),
                "classes": meta.get("classes", []),
                "text": meta.get("text", ""),
                "styles": meta.get("styles", {}),
                "index": idx,
            })
        return dom_elements

    def load_pyodide(self) -> bool:
        """Load Pyodide runtime (called externally)."""
        self._pyodide_loaded = True
        return True

    def is_available(self) -> bool:
        """Check if Pyodide is available."""
        return True


def create_fallback(
    container_width: float = 1280.0,
    container_height: float = 720.0,
) -> PyodideFallback:
    """
    Factory function to create a Pyodide fallback adapter.
    
    Args:
        container_width: Width of the container.
        container_height: Height of the container.
        
    Returns:
        PyodideFallback instance.
    """
    return PyodideFallback(
        container_width=container_width,
        container_height=container_height,
    )