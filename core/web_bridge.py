# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Aether-Web Bridge: Translates physics state to DOM coordinates.

This module acts as the translator layer between the AetherEngine's
internal StateTensor (float32 arrays) and the Web's DOM (HTML/CSS).
It handles ID mapping, coordinate synchronization, and safety checks
to ensure no NaN/Inf values leak to the browser.
"""
import json
import time
import os
import numpy as np
from typing import Dict, List, Any, Optional
from core.aether_math import StateTensor

# Security limits
_MAX_ELEMENTS_PER_SYNC = int(os.environ.get("AETHERIS_MAX_ELEMENTS", "10000"))
_CHUNK_SIZE = int(os.environ.get("AETHERIS_SYNC_CHUNK_SIZE", "500"))


class WebBridge:
    """
    Synchronizes AetherEngine elements with Web DOM elements.

    Maintains a mapping between internal element indices and HTML IDs,
    generates JSON payloads for coordinate updates, and validates
    data integrity before transmission.
    """

    def __init__(self, container_width: float = 1280.0, container_height: float = 720.0):
        self._container_w = container_width
        self._container_h = container_height
        self._element_map: Dict[int, str] = {}  # index -> html_id
        self._metadata: Dict[str, Dict[str, Any]] = {}  # html_id -> {tag, text, classes, ...}
        self._last_sync_time = 0.0
        self._sync_count = 0

    def register_element(self, index: int, html_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register an element from the engine with a corresponding HTML ID."""
        self._element_map[index] = html_id
        if metadata:
            self._metadata[html_id] = metadata
        else:
            self._metadata[html_id] = {"tag": "div", "classes": [], "text": ""}

    def unregister_element(self, index: int) -> None:
        """Remove an element from the bridge."""
        html_id = self._element_map.pop(index, None)
        if html_id:
            self._metadata.pop(html_id, None)

    def get_html_id(self, index: int) -> Optional[str]:
        """Get the HTML ID for a given engine index."""
        return self._element_map.get(index)

    def get_element_metadata(self, html_id: str) -> Dict[str, Any]:
        """Get the HTML metadata (tag, classes, text) for an element."""
        return self._metadata.get(html_id, {"tag": "div", "classes": [], "text": ""})

    def sync(self, elements: List[Any]) -> str:
        """
        Generate a JSON payload of current element positions for the web client.

        Args:
            elements: List of DifferentialElement objects from AetherEngine.

        Returns:
            JSON string: {"frame": N, "elements": [{"id": "...", "x": 0, "y": 0, "w": 0, "h": 0}, ...]}
        """
        self._sync_count += 1
        self._last_sync_time = time.perf_counter()

        # Security: Limit elements to prevent DoS
        if len(elements) > _MAX_ELEMENTS_PER_SYNC:
            elements = elements[:_MAX_ELEMENTS_PER_SYNC]

        payload = {
            "frame": self._sync_count,
            "timestamp": self._last_sync_time,
            "elements": [],
            "truncated": len(elements) < len(elements) if hasattr(elements, '__len__') else False
        }

        for idx, elem in enumerate(elements):
            # Chunk processing to avoid blocking
            if idx % _CHUNK_SIZE == 0 and idx > 0:
                # Yield to prevent blocking (simplified chunking)
                pass

            html_id = self._element_map.get(idx)
            if not html_id:
                continue

            state = elem.tensor.state
            x, y, w, h = float(state[0]), float(state[1]), float(state[2]), float(state[3])

            # Aether-Guard: NaN/Inf protection BEFORE clamping
            if not (np.isfinite(x) and np.isfinite(y) and np.isfinite(w) and np.isfinite(h)):
                continue

            # Aether-Guard: Clamp coordinates to container bounds
            x = max(0.0, min(x, self._container_w - w))
            y = max(0.0, min(y, self._container_h - h))

            payload["elements"].append({
                "id": html_id,
                "x": round(x, 2),
                "y": round(y, 2),
                "w": round(w, 2),
                "h": round(h, 2),
                "z": getattr(elem, '_z_index', idx)
            })

        return json.dumps(payload)

    def get_initial_dom_state(self) -> List[Dict[str, Any]]:
        """
        Generate the initial HTML structure needed to render all elements.

        Returns:
            List of dicts with HTML creation instructions.
        """
        dom_elements = []
        for idx, html_id in self._element_map.items():
            meta = self._metadata.get(html_id, {})
            dom_elements.append({
                "id": html_id,
                "tag": meta.get("tag", "div"),
                "classes": meta.get("classes", []),
                "text": meta.get("text", ""),
                "styles": meta.get("styles", {}),
                "index": idx
            })
        return dom_elements

    @property
    def element_count(self) -> int:
        return len(self._element_map)

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "elements": self.element_count,
            "sync_frames": self._sync_count,
            "last_sync": self._last_sync_time
        }
