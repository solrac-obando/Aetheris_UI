# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
LightWASM Adapter: Backwards-compatible wrapper with automatic fallback.

This module provides a lightweight alternative to Pyodide for web rendering,
using the Adapter Pattern to seamlessly switch between JSRenderer (lightweight)
and Pyodide (full-featured) based on browser capabilities.
"""
import json
import os
import time
import math
from typing import Any, Dict, List, Optional

from core.aether_math import StateTensor

_USE_LIGHT_WASM = os.environ.get("AETHERIS_USE_LIGHT_WASM", "true").lower() == "true"
_USE_WEBGL = os.environ.get("AETHERIS_USE_WEBGL", "false").lower() == "true"

# Dynamic limits based on hardware
try:
    from core.dynamic_limits import get_optimal_max_elements, get_system_profile
    _SYSTEM_PROFILE = get_system_profile()
    _DEFAULT_MAX_ELEMENTS = _SYSTEM_PROFILE["bridge_limit"]
except ImportError:
    _DEFAULT_MAX_ELEMENTS = int(os.environ.get("AETHERIS_MAX_ELEMENTS", "20000"))

# Security limits (default high for tests, lower for production)
_MAX_ELEMENTS = int(os.environ.get("AETHERIS_MAX_ELEMENTS", str(_DEFAULT_MAX_ELEMENTS)))
_MAX_SYNC_MS = float(os.environ.get("AETHERIS_MAX_SYNC_MS", "500.0"))  # Max 500ms per sync
_DOS_DETECTION_THRESHOLD = 10  # Number of slow syncs before DoS alert


class LightWASMAdapter:
    """
    Lightweight WASM adapter with automatic fallback to Pyodide.
    
    Maintains the SAME public API as WebBridge for backwards compatibility.
    Automatically detects browser capabilities and selects the appropriate renderer.
    
    Usage:
        from wasm.light_wasm_adapter import LightWASMAdapter
        adapter = LightWASMAdapter()  # Same signature as WebBridge
        adapter.sync(elements)         # Same method
    """

    def __init__(
        self,
        container_width: float = 1280.0,
        container_height: float = 720.0,
        use_light_wasm: Optional[bool] = None,
        use_webgl: Optional[bool] = None,
    ):
        self._container_w = container_width
        self._container_h = container_height
        self._element_map: Dict[int, str] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._last_sync_time = 0.0
        self._sync_count = 0

        self._use_light_wasm = (
            use_light_wasm if use_light_wasm is not None else _USE_LIGHT_WASM
        )
        self._use_webgl = use_webgl if use_webgl is not None else _USE_WEBGL

        self._adapter = None
        self._fallback_mode = False

        if self._use_light_wasm:
            try:
                from wasm.adapters.js_renderer import JSRenderer

                self._adapter = JSRenderer(
                    container_width=container_width,
                    container_height=container_height,
                    use_webgl=use_webgl if use_webgl is not None else False,
                )
            except ImportError:
                self._fallback_mode = True
                self._use_light_wasm = False

    @property
    def element_count(self) -> int:
        return len(self._element_map)

    @property
    def stats(self) -> Dict[str, Any]:
        adapter_info = {}
        if self._adapter:
            adapter_info = self._adapter.stats
        return {
            "elements": self.element_count,
            "sync_frames": self._sync_count,
            "last_sync": self._last_sync_time,
            "adapter": self.adapter_type,
            "fallback_mode": self._fallback_mode,
            **adapter_info,
        }

    @property
    def adapter_type(self) -> str:
        if self._fallback_mode:
            return "pyodide"
        elif self._adapter:
            return self._adapter.adapter_type
        return "unknown"

    @property
    def bundle_size(self) -> int:
        if self._fallback_mode:
            return 40 * 1024 * 1024
        elif self._adapter:
            return self._adapter.bundle_size
        return 0

    def register_element(
        self, index: int, html_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        self._element_map[index] = html_id
        if metadata:
            self._metadata[html_id] = metadata
        else:
            self._metadata[html_id] = {"tag": "div", "classes": [], "text": ""}

        if self._adapter:
            self._adapter.register_element(index, html_id, metadata)

    def unregister_element(self, index: int) -> None:
        html_id = self._element_map.pop(index, None)
        if html_id:
            self._metadata.pop(html_id, None)

        if self._adapter:
            self._adapter.unregister_element(index)

    def get_html_id(self, index: int) -> Optional[str]:
        return self._element_map.get(index)

    def get_element_metadata(self, html_id: str) -> Dict[str, Any]:
        return self._metadata.get(html_id, {"tag": "div", "classes": [], "text": ""})

    def sync(self, elements: List[Any]) -> str:
        """
        Generate a JSON payload of current element positions for the web client.
        
        This method maintains the SAME signature as WebBridge.sync() for
        backwards compatibility. The implementation switches between
        JSRenderer and Pyodide based on configuration.
        
        Args:
            elements: List of DifferentialElement objects from AetherEngine.
            
        Returns:
            JSON string: {"frame": N, "elements": [{"id": "...", "x": 0, "y": 0, "w": 0, "h": 0}, ...]}
        """
        sync_start = time.perf_counter()

        # Security: Limit elements to prevent DoS
        if len(elements) > _MAX_ELEMENTS:
            elements = elements[:_MAX_ELEMENTS]

        self._sync_count += 1
        self._last_sync_time = sync_start

        if self._adapter and not self._fallback_mode:
            result = self._adapter.sync(elements, self._element_map, self._metadata)
        else:
            result = self._sync_fallback(elements)

        # Monitor latency for DoS detection
        elapsed_ms = (time.perf_counter() - sync_start) * 1000
        if elapsed_ms > _MAX_SYNC_MS:
            self._slow_sync_count = getattr(self, '_slow_sync_count', 0) + 1
            if self._slow_sync_count > _DOS_DETECTION_THRESHOLD:
                raise RuntimeError(
                    f"Security: DoS attack detected. Sync latency {elapsed_ms:.2f}ms "
                    f"exceeded {_MAX_SYNC_MS}ms threshold for {_DOS_DETECTION_THRESHOLD} consecutive times."
                )

        return result

    def _sync_fallback(self, elements: List[Any]) -> str:
        """Fallback sync implementation using Pyodide-compatible format."""
        payload = {
            "frame": self._sync_count,
            "timestamp": self._last_sync_time,
            "elements": [],
        }

        for idx, elem in enumerate(elements):
            html_id = self._element_map.get(idx)
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

            if not (
                self._is_finite(x)
                and self._is_finite(y)
                and self._is_finite(w)
                and self._is_finite(h)
            ):
                continue

            if abs(x) > 1e10 or abs(y) > 1e10 or abs(w) > 1e10 or abs(h) > 1e10:
                continue

            x = max(0.0, min(x, self._container_w - w))
            y = max(0.0, min(y, self._container_h - h))

            if abs(x) > 1e9 or abs(y) > 1e9 or abs(w) > 1e9 or abs(h) > 1e9:
                continue

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

    def detect_capabilities(self) -> Dict[str, bool]:
        """Detect browser capabilities for adapter selection."""
        capabilities = {
            "canvas_2d": True,
            "webgl": False,
            "webgl2_compute": False,
            "wasm": True,
            "worker_threads": True,
        }

        if self._adapter:
            capabilities.update(self._adapter.detect_capabilities())

        return capabilities

    def set_preferred_adapter(self, adapter_type: str) -> None:
        """Manually set the preferred adapter type."""
        if adapter_type == "js_renderer":
            self._fallback_mode = False
            if not self._adapter:
                from wasm.adapters.js_renderer import JSRenderer

                self._adapter = JSRenderer(
                    container_width=self._container_w,
                    container_height=self._container_h,
                    use_webgl=self._use_webgl,
                )
        elif adapter_type == "pyodide":
            self._fallback_mode = True
            self._adapter = None


def create_adapter(
    container_width: float = 1280.0,
    container_height: float = 720.0,
    force_adapter: Optional[str] = None,
) -> LightWASMAdapter:
    """
    Factory function to create a LightWASMAdapter.
    
    This is the RECOMMENDED way to create an adapter instance,
    as it handles all initialization logic.
    
    Args:
        container_width: Width of the container.
        container_height: Height of the container.
        force_adapter: Force a specific adapter ("js_renderer", "pyodide", "webgl").
        
    Returns:
        LightWASMAdapter instance.
    """
    adapter = LightWASMAdapter(
        container_width=container_width,
        container_height=container_height,
    )

    if force_adapter:
        adapter.set_preferred_adapter(force_adapter)

    return adapter