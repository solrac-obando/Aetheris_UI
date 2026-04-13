# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Headless Texture Bridge - Strategy 3: Embeddable Framework.

This module provides the foundation for embedding Aetheris into external
UI frameworks (like Flet, PyQt, Tkinter, or web frameworks).

Instead of opening a window, this bridge connects to the AetherEngine
and exposes raw frame data that can be consumed as a texture by
external frameworks.

MATHEMATICAL MODEL:
===================

Frame Buffer Format:
  - Each element contributes [x, y, w, h, r, g, b, a, z, vx, vy] = 11 floats
  - Total buffer = num_elements * 11 * 4 bytes (float32)
  
Coordinate Transformation:
  - Engine uses normalized coordinates (0-1 range internally)
  - Headless bridge denormalizes to pixel coordinates: pixel = coord * dimension
  - This allows external frameworks to render directly without conversion

Texture Output Formats:
  1. Raw numpy array (dense format)
  2. JSON serialized (for web/remote)
  3. Base64 encoded PNG (for UI frameworks that accept images)
"""

from __future__ import annotations

import json
import base64
import io
import time
from typing import Optional, Literal, Any
from dataclasses import dataclass

import numpy as np

# Import AetherEngine - use try/except to handle the case where engine might not be loaded yet
try:
    from core.engine import AetherEngine as _AetherEngineType
except ImportError:
    _AetherEngineType = Any


@dataclass
class FrameMetadata:
    """Metadata accompanying each frame."""
    frame_number: int
    timestamp: float
    element_count: int
    fps: float
    engine_time_ms: float


@dataclass
class FrameBuffer:
    """Complete frame data including state and metadata."""
    states: np.ndarray  # Shape: (N, 11) - [x, y, w, h, r, g, b, a, z, vx, vy]
    metadata: FrameMetadata
    raw_bytes: Optional[bytes] = None


class HeadlessTextureBridge:
    """
    Headless bridge for embedding Aetheris into external frameworks.
    
    This class connects to the AetherEngine without creating any window,
    and provides raw frame data that external frameworks can consume
    as a live texture.
    
    Usage:
        bridge = HeadlessTextureBridge(engine)
        while True:
            frame = bridge.get_frame_buffer()
            # frame.states contains element positions/colors
            # Pass to external framework as texture
    """
    
    def __init__(
        self,
        engine: "AetherEngine",
        output_format: Literal["numpy", "json", "base64"] = "numpy",
        frame_width: int = 1280,
        frame_height: int = 720,
    ) -> None:
        """
        Initialize the headless bridge.
        
        Args:
            engine: The AetherEngine instance to connect to
            output_format: Format for frame data output
            frame_width: Width of output frame in pixels
            frame_height: Height of output frame in pixels
        """
        self._engine = engine
        self._output_format = output_format
        self._frame_width = frame_width
        self._frame_height = frame_height
        
        # Frame tracking
        self._frame_count = 0
        self._start_time = time.perf_counter()
        self._last_frame_time = self._start_time
        self._last_fps = 0.0
        
        # Buffer for element states
        # Format: [x, y, w, h, r, g, b, a, z, vx, vy] = 11 floats per element
        self._state_dim = 11
        
        # Denormalization factors (engine uses 0-1 normalized coords)
        self._denorm_w = float(frame_width)
        self._denorm_h = float(frame_height)
    
    @property
    def engine(self) -> "AetherEngine":
        """Get the connected AetherEngine."""
        return self._engine
    
    @property
    def frame_width(self) -> int:
        return self._frame_width
    
    @property
    def frame_height(self) -> int:
        return self._frame_height
    
    @property
    def frame_count(self) -> int:
        return self._frame_count
    
    @property
    def current_fps(self) -> float:
        return self._last_fps
    
    def tick(self) -> np.ndarray:
        """
        Advance the engine by one tick and return state.
        
        This is a convenience method that ticks the engine and returns
        the raw state array. For more control, use get_frame_buffer().
        
        Returns:
            numpy array of shape (N, 11) with element states
        """
        # Tick the engine
        self._engine.tick(self._frame_width, self._frame_height)
        
        # Get the state
        return self.get_element_states()
    
    def get_element_states(self) -> np.ndarray:
        """
        Get current element states as a numpy array.
        
        Returns:
            numpy array of shape (N, 11) where each row is:
            [x, y, w, h, r, g, b, a, z, vx, vy]
            
            - x, y: Position in pixels (denormalized from 0-1)
            - w, h: Dimensions in pixels
            - r, g, b, a: Color components (0-1)
            - z: Z-index for layering
            - vx, vy: Velocity components (for physics)
        """
        elements = self._engine.get_all_elements()
        
        if not elements:
            return np.zeros((0, self._state_dim), dtype=np.float32)
        
        states = np.zeros((len(elements), self._state_dim), dtype=np.float32)
        
        for i, elem in enumerate(elements):
            # Get state tensor from element
            tensor = elem.tensor
            state = tensor.state
            
            # Extract position and size (denormalize from 0-1 to pixels)
            x = float(state[0]) * self._denorm_w
            y = float(state[1]) * self._denorm_h
            w = float(state[2]) * self._denorm_w
            h = float(state[3]) * self._denorm_h
            
            # Aether-Guard: Replace NaN/Inf with 0 for safety
            if not np.isfinite(x):
                x = 0.0
            if not np.isfinite(y):
                y = 0.0
            if not np.isfinite(w):
                w = 0.0
            if not np.isfinite(h):
                h = 0.0
            
            # Extract color (stored as RGBA 0-1)
            color = elem._color
            r = float(color[0]) if len(color) > 0 else 1.0
            g = float(color[1]) if len(color) > 1 else 1.0
            b = float(color[2]) if len(color) > 2 else 1.0
            a = float(color[3]) if len(color) > 3 else 1.0
            
            # Aether-Guard: Validate color values
            if not np.isfinite(r):
                r = 1.0
            if not np.isfinite(g):
                g = 1.0
            if not np.isfinite(b):
                b = 1.0
            if not np.isfinite(a):
                a = 1.0
            
            # Z-index
            z = float(elem._z_index)
            
            # Velocity (if available)
            if hasattr(tensor, 'velocity') and tensor.velocity is not None:
                vx = float(tensor.velocity[0])
                vy = float(tensor.velocity[1])
            else:
                vx, vy = 0.0, 0.0
            
            states[i] = [x, y, w, h, r, g, b, a, z, vx, vy]
        
        return states
    
    def get_frame_buffer(
        self,
        format: Optional[Literal["numpy", "json", "base64"]] = None,
    ) -> FrameBuffer:
        """
        Get the current frame as a complete buffer with metadata.
        
        This is the primary method for external frameworks to consume
        Aetheris frames as textures.
        
        Args:
            format: Optional format override (defaults to instance setting)
            
        Returns:
            FrameBuffer containing states and metadata
        """
        # Update frame tracking
        current_time = time.perf_counter()
        self._frame_count += 1
        
        # Calculate FPS
        elapsed = current_time - self._start_time
        if elapsed > 0:
            self._last_fps = self._frame_count / elapsed
        
        # Calculate last frame duration
        frame_duration_ms = (current_time - self._last_frame_time) * 1000.0
        self._last_frame_time = current_time
        
        # Get element states
        states = self.get_element_states()
        
        # Build metadata
        metadata = FrameMetadata(
            frame_number=self._frame_count,
            timestamp=current_time,
            element_count=len(states),
            fps=self._last_fps,
            engine_time_ms=frame_duration_ms,
        )
        
        # Format output
        output_format = format or self._output_format
        raw_bytes: Optional[bytes] = None
        
        if output_format == "numpy":
            raw_bytes = states.tobytes()
        elif output_format == "json":
            raw_bytes = self._states_to_json(states).encode('utf-8')
        elif output_format == "base64":
            # For base64, we embed the JSON in the frame buffer
            json_str = self._states_to_json(states)
            raw_bytes = base64.b64encode(json_str.encode('utf-8'))
        
        return FrameBuffer(
            states=states,
            metadata=metadata,
            raw_bytes=raw_bytes,
        )
    
    def _states_to_json(self, states: np.ndarray) -> str:
        """Convert state array to JSON string."""
        elements = []
        
        for row in states:
            elements.append({
                "x": round(float(row[0]), 2),
                "y": round(float(row[1]), 2),
                "w": round(float(row[2]), 2),
                "h": round(float(row[3]), 2),
                "color": {
                    "r": round(float(row[4]), 3),
                    "g": round(float(row[5]), 3),
                    "b": round(float(row[6]), 3),
                    "a": round(float(row[7]), 3),
                },
                "z": int(row[8]),
                "velocity": {
                    "x": round(float(row[9]), 3),
                    "y": round(float(row[10]), 3),
                },
            })
        
        return json.dumps({
            "frame": self._frame_count,
            "timestamp": self._last_frame_time,
            "fps": round(self._last_fps, 2),
            "width": self._frame_width,
            "height": self._frame_height,
            "element_count": len(elements),
            "elements": elements,
        })
    
    def get_frame_as_image(self) -> bytes:
        """
        Get current frame as raw image bytes (PNG format).
        
        This creates a simple visual representation of the current frame
        that can be displayed in any image viewer or used as a texture.
        
        Returns:
            PNG image bytes
        """
        try:
            from PIL import Image
        except ImportError:
            # Fallback: return placeholder if PIL not available
            return b""
        
        states = self.get_element_states()
        
        # Create RGBA image
        image = Image.new('RGBA', (self._frame_width, self._frame_height), (0, 0, 0, 0))
        pixels = image.load()
        
        for row in states:
            x, y, w, h = int(row[0]), int(row[1]), int(row[2]), int(row[3])
            r, g, b, a = int(row[4] * 255), int(row[5] * 255), int(row[6] * 255), int(row[7] * 255)
            
            # Fill rectangle
            for py in range(y, min(y + h, self._frame_height)):
                for px in range(x, min(x + w, self._frame_width)):
                    pixels[px, py] = (r, g, b, a)
        
        # Convert to bytes
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return buffer.getvalue()
    
    def get_frame_base64(self) -> str:
        """
        Get current frame as Base64 encoded PNG.
        
        Useful for web frameworks or returning as data URI.
        
        Returns:
            Base64 encoded PNG string (without data:image prefix)
        """
        png_bytes = self.get_frame_as_image()
        return base64.b64encode(png_bytes).decode('utf-8')
    
    def get_json_snapshot(self) -> str:
        """
        Get complete frame state as JSON string.
        
        This is the most detailed output format, useful for debugging,
        web transmission, or saving snapshots.
        
        Returns:
            JSON string with full frame state
        """
        states = self.get_element_states()
        return self._states_to_json(states)
    
    def get_flat_buffer(self) -> np.ndarray:
        """
        Get frame as a flat numpy array for GPU/texture upload.
        
        Useful for direct GPU texture creation (e.g., with OpenGL or CUDA).
        
        Returns:
            Flat numpy array of all frame data
        """
        states = self.get_element_states()
        
        # Add metadata as additional channels
        metadata_array = np.array([
            self._frame_count,
            self._frame_width,
            self._frame_height,
            self._last_fps,
        ], dtype=np.float32)
        
        # Flatten and concatenate
        flat = states.flatten()
        return np.concatenate([flat, metadata_array])
    
    def reset(self) -> None:
        """Reset frame tracking and clear state."""
        self._frame_count = 0
        self._start_time = time.perf_counter()
        self._last_frame_time = self._start_time
        self._last_fps = 0.0
    
    def __repr__(self) -> str:
        return (
            f"HeadlessTextureBridge("
            f"format={self._output_format}, "
            f"size={self._frame_width}x{self._frame_height}, "
            f"frames={self._frame_count}, "
            f"fps={self._last_fps:.1f})"
        )


__all__ = [
    "HeadlessTextureBridge",
    "FrameMetadata",
    "FrameBuffer",
]