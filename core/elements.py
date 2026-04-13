# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

from abc import ABC, abstractmethod
import numpy as np
from core.aether_math import StateTensor
from core.lifecycle import DisposableMixin


class DifferentialElement(DisposableMixin, ABC):
    """Abstract base class for all UI elements in Aetheris.
    
    Each element owns a StateTensor that represents its current physical state
    [x, y, width, height] and evolves through forces and integration.
    
    Inherits from DisposableMixin for lifecycle management:
    - dispose() method available on all elements
    - Context manager support (with element as e)
    """
    
    def __init__(self, x=0, y=0, w=100, h=100, color=(1, 1, 1, 1), z=0,
                 sound_trigger=None):
        """Initialize a differential element.
        
        Args:
            x, y: Position coordinates
            w, h: Width and height dimensions
            color: RGBA tuple (float32, values 0-1)
            z: Z-index for rendering depth
            sound_trigger: Sound trigger spec, e.g. 'impact:0.8' or
                          'on:click_sound;off:release_sound' or 'settle'
        """
        DisposableMixin.__init__(self)
        self.tensor = StateTensor(x, y, w, h)
        self._color = np.array(color, dtype=np.float32)
        self._z_index = z
        self._sound_trigger = sound_trigger
        self._sound_triggered_this_frame = False
        self._prev_velocity_mag = 0.0

    def dispose(self) -> None:
        """Override dispose to clean up element-specific resources."""
        self.tensor = None
        self._color = None
        self._sound_trigger = None
        super().dispose()

    @property
    def sound_trigger(self):
        return self._sound_trigger

    @sound_trigger.setter
    def sound_trigger(self, value):
        self._sound_trigger = value

    def evaluate_sound_trigger(self, bridge=None) -> bool:
        """Evaluate sound trigger conditions based on current physics state.

        Supported trigger formats:
        - 'impact:0.8' — trigger when velocity L2 norm exceeds 0.8
        - 'settle' — trigger when epsilon-snapping occurs
        - 'on:click_sound;off:release_sound' — multi-sound state definition
        - 'collision:wall_bounce' — trigger on boundary collision

        Args:
            bridge: Optional AetherAudioBridge instance

        Returns:
            True if a sound was triggered
        """
        if not self._sound_trigger:
            return False

        self._sound_triggered_this_frame = False
        trigger = self._sound_trigger

        if ';' in trigger:
            return self._evaluate_multi_sound(trigger, bridge)

        if trigger == 'settle':
            vel_mag = np.linalg.norm(self.tensor.velocity)
            if vel_mag < 0.1 and self._prev_velocity_mag >= 0.1:
                self._sound_triggered_this_frame = True
                if bridge:
                    bridge.play_sound('settle', volume=0.3, pitch=1.0)
                return True

        if trigger.startswith('impact:'):
            try:
                threshold = float(trigger.split(':')[1])
            except (ValueError, IndexError):
                threshold = 0.5
            vel_mag = np.linalg.norm(self.tensor.velocity)
            if vel_mag > threshold and self._prev_velocity_mag <= threshold:
                self._sound_triggered_this_frame = True
                vol = min(vel_mag / 10.0, 1.0)
                if bridge:
                    bridge.play_sound('impact', volume=vol, pitch=1.0)
                return True

        if trigger.startswith('collision:'):
            try:
                sound_id = trigger.split(':', 1)[1]
            except IndexError:
                sound_id = 'collision'
            acc_mag = np.linalg.norm(self.tensor.acceleration)
            if acc_mag > 50.0:
                self._sound_triggered_this_frame = True
                if bridge:
                    bridge.play_sound(sound_id, volume=min(acc_mag / 200.0, 1.0), pitch=1.0)
                return True

        self._prev_velocity_mag = float(np.linalg.norm(self.tensor.velocity))
        return False

    def _evaluate_multi_sound(self, trigger: str, bridge=None) -> bool:
        """Evaluate multi-sound trigger like 'on:click;off:release'."""
        parts = trigger.split(';')
        for part in parts:
            if ':' in part:
                state, sound_id = part.split(':', 1)
                state = state.strip().lower()
                sound_id = sound_id.strip()
                if state == 'on' or state == 'active':
                    vel_mag = np.linalg.norm(self.tensor.velocity)
                    if vel_mag > 0.5 and self._prev_velocity_mag <= 0.5:
                        self._sound_triggered_this_frame = True
                        if bridge:
                            bridge.play_sound(sound_id, volume=0.5, pitch=1.0)
                        return True
                elif state == 'off' or state == 'inactive':
                    vel_mag = np.linalg.norm(self.tensor.velocity)
                    if vel_mag < 0.1 and self._prev_velocity_mag >= 0.1:
                        self._sound_triggered_this_frame = True
                        if bridge:
                            bridge.play_sound(sound_id, volume=0.3, pitch=0.8)
                        return True
        self._prev_velocity_mag = float(np.linalg.norm(self.tensor.velocity))
        return False

    @abstractmethod
    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        """Calculates the target [x, y, w, h] for the solver.
        
        This is the core logic where each element type defines its desired
        target state based on environmental constraints.
        
        Args:
            container_w: Width of the container/window
            container_h: Height of the container/window
            
        Returns:
            numpy.array: Target state [x, y, w, h] as float32
        """
        pass

    @property
    def rendering_data(self):
        """Returns data needed for rendering the element.
        
        Note: For zero-allocation tick, use the direct properties instead:
        element.rect, element.color, element.z_index
        
        Returns:
            dict: Contains rect (StateTensor.state), color, and z_index
        """
        return {
            "rect": self.tensor.state,
            "color": self._color,
            "z": self._z_index
        }

    @property
    def rect(self):
        """Direct access to StateTensor.state for zero-allocation rendering.
        
        Returns:
            numpy.ndarray: Reference to [x, y, width, height] state vector
        """
        return self.tensor.state

    @property
    def color(self):
        """Direct access to color array for zero-allocation rendering.
        
        Returns:
            numpy.ndarray: Reference to [r, g, b, a] color vector
        """
        return self._color

    @property
    def z_index(self):
        """Direct access to z-index for zero-allocation rendering.
        
        Returns:
            int: Z-index for rendering depth
        """
        return self._z_index

    @property
    def metadata(self):
        """Optional metadata for renderer-specific data (text, fonts, etc.).
        
        Override in subclasses that need to expose non-physics data to renderers.
        Returns None by default so the engine can skip elements without metadata.
        
        Returns:
            dict or None: Renderer-specific metadata, or None if not applicable.
        """
        return None


class StaticBox(DifferentialElement):
    """A simple static box element that maintains a fixed target position.
    
    Unlike responsive elements, StaticBox always returns the same target
    regardless of container size.
    """
    
    def __init__(self, x, y, w, h, color=(1, 1, 1, 1), z=0, sound_trigger=None):
        """Initialize a static box with fixed target rectangle.
        
        Args:
            x, y: Position of the target rectangle
            w, h: Width and height of the target rectangle
            color: RGBA tuple (float32, values 0-1)
            z: Z-index for rendering depth
            sound_trigger: Sound trigger spec
        """
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._target_rect = np.array([x, y, w, h], dtype=np.float32)

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        """Return the fixed target rectangle as the asymptote.
        
        Ignores container size since this is a static element.
        """
        return self._target_rect.copy()


class SmartPanel(DifferentialElement):
    """A responsive panel that maintains percentage-based padding from container edges.
    
    By default, maintains 5% padding on all sides, adapting to container size changes.
    """
    
    def __init__(self, x=0, y=0, w=100, h=100, color=(1, 1, 1, 1), z=0, padding=0.05, sound_trigger=None):
        """Initialize a smart panel.
        
        Args:
            x, y: Initial position (will be overridden by asymptote calculation)
            w, h: Initial dimensions (will be overridden by asymptote calculation)
            color: RGBA tuple (float32, values 0-1)
            z: Z-index for rendering depth
            padding: Fraction of container to maintain as padding (0.05 = 5%)
            sound_trigger: Sound trigger spec
        """
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._padding = padding

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        """Calculate target rectangle with percentage-based padding.
        
        Applies linear scaling (Escalamiento Lineal) from Álgebra de Baldor:
        - Position: container * padding
        - Dimensions: container * (1 - 2*padding)
        
        Args:
            container_w: Width of the container/window
            container_h: Height of the container/window
            
        Returns:
            numpy.array: Target state [x, y, w, h] as float32
        """
        # Linear scaling transformation: map [0, container] to [padding*container, (1-padding)*container]
        x = container_w * self._padding
        y = container_h * self._padding
        w = container_w * (1.0 - 2.0 * self._padding)
        h = container_h * (1.0 - 2.0 * self._padding)
        
        return np.array([x, y, w, h], dtype=np.float32)


class FlexibleTextNode(DifferentialElement):
    """A text element that can be positioned and sized relative to container.
    
    For simplicity in Phase 8, this behaves like a StaticBox but with text-specific defaults.
    In future phases, it would integrate with text rendering systems.
    """
    
    def __init__(self, x=0, y=0, w=200, h=50, color=(1, 1, 1, 1), z=0, text="Text", sound_trigger=None):
        """Initialize a flexible text node.
        
        Args:
            x, y: Position coordinates
            w, h: Width and height dimensions
            color: RGBA tuple (float32, values 0-1)
            z: Z-index for rendering depth
            text: The text content to display
            sound_trigger: Sound trigger spec
        """
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._text = text
        # For now, treat as static element - future versions will have text-specific layout logic

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        """Return fixed target rectangle (static behavior for now).
        
        In Phase 8, we use static positioning. Future phases will implement
        text wrapping, alignment, and responsive text sizing.
        """
        # Return current state as target (static behavior)
        return self.tensor.state.copy()
        
    @property
    def text(self):
        """Get the text content."""
        return self._text
        
    @text.setter
    def text(self, value):
        """Set the text content."""
        self._text = value


class SmartButton(DifferentialElement):
    """A button element that anchors to a parent element with offsets.
    
    The button maintains a fixed offset from its parent's position,
    allowing for relative positioning that stays consistent when the parent moves.
    """
    
    def __init__(self, parent, offset_x=0, offset_y=0, offset_w=100, offset_h=50, 
                 color=(0.8, 0.8, 0.2, 1.0), z=0, sound_trigger=None):
        """Initialize a smart button anchored to a parent.
        
        Args:
            parent: The parent DifferentialElement to anchor to
            offset_x: X offset from parent's left edge
            offset_y: Y offset from parent's top edge
            offset_w: Width of the button
            offset_h: Height of the button
            color: RGBA tuple (float32, values 0-1)
            z: Z-index for rendering depth
            sound_trigger: Sound trigger spec
        """
        super().__init__(
            parent.tensor.state[0] + offset_x,
            parent.tensor.state[1] + offset_y,
            offset_w,
            offset_h,
            color,
            z
        )
        self._parent = parent
        self._offset_x = offset_x
        self._offset_y = offset_y
        self._offset_w = offset_w
        self._offset_h = offset_h

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        """Calculate target position based on parent's current position plus offset.
        
        The button dynamically follows its parent by calculating asymptotes
        based on the parent's current state (which includes physics simulation).
        
        Args:
            container_w: Width of the container/window (unused, kept for interface consistency)
            container_h: Height of the container/window (unused, kept for interface consistency)
            
        Returns:
            numpy.array: Target state [x, y, w, h] as float32
        """
        # Get parent's current position
        parent_state = self._parent.tensor.state
        
        # Calculate target: parent position + offset
        target_x = parent_state[0] + self._offset_x
        target_y = parent_state[1] + self._offset_y
        target_w = self._offset_w
        target_h = self._offset_h
        
        return np.array([target_x, target_y, target_w, target_h], dtype=np.float32)


class CanvasTextNode(DifferentialElement):
    """A text element rendered directly on the Canvas via ctx.fillText.
    
    This element participates fully in the physics simulation (Hooke's Law,
    boundary forces, Epsilon Snapping) but its text metadata is exposed
    separately via the engine's get_ui_metadata() JSON bridge since the
    Structured NumPy Array cannot hold strings.
    
    Ideal for high-performance, non-selectable text like game scores,
    trivia cards, or animated labels.
    """
    
    # Element type marker for the metadata bridge
    _element_type = "canvas_text"
    
    def __init__(self, x=0, y=0, w=200, h=50, color=(1, 1, 1, 1), z=0,
                 text="Text", font_size=24, font_family="Arial", sound_trigger=None):
        """Initialize a canvas text node.
        
        Args:
            x, y: Position coordinates (physics-driven)
            w, h: Width and height dimensions (physics-driven)
            color: RGBA tuple (float32, values 0-1) for the text color
            z: Z-index for rendering depth
            text: The text content to display
            font_size: Font size in pixels
            font_family: Font family name
            sound_trigger: Sound trigger spec
        """
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._text = text
        self._font_size = font_size
        self._font_family = font_family

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        """Return fixed target rectangle (static text positioning).
        
        The text node maintains its initial position as its asymptote.
        Future phases may implement responsive text sizing and wrapping.
        """
        return self.tensor.state.copy()
    
    @property
    def text(self):
        """Get the text content."""
        return self._text
    
    @text.setter
    def text(self, value):
        """Set the text content."""
        self._text = value
    
    @property
    def font_size(self):
        """Get the font size in pixels."""
        return self._font_size
    
    @font_size.setter
    def font_size(self, value):
        """Set the font size in pixels."""
        self._font_size = value
    
    @property
    def font_family(self):
        """Get the font family name."""
        return self._font_family
    
    @font_family.setter
    def font_family(self, value):
        """Set the font family name."""
        self._font_family = value
    
    @property
    def text_metadata(self):
        """Get text metadata for the JSON metadata bridge.
        
        Returns:
            dict: Text rendering metadata for the JS renderer
        """
        return {
            "type": "canvas_text",
            "text": self._text,
            "size": self._font_size,
            "family": self._font_family,
            "color": self._color.tolist(),
        }

    @property
    def metadata(self):
        """Text metadata for renderer bridge. Overrides DifferentialElement.metadata."""
        return self.text_metadata


class DOMTextNode(DifferentialElement):
    """A text element rendered as an HTML <div> overlaid on the Canvas.
    
    This element participates fully in the physics simulation (Hooke's Law,
    boundary forces, Epsilon Snapping) but its text metadata is exposed
    separately via the engine's get_ui_metadata() JSON bridge.
    
    The JS renderer creates/updates actual DOM elements positioned via
    hardware-accelerated CSS transforms (translate3d), enabling:
    - Text selection
    - Accessibility (screen readers)
    - SEO (searchable content)
    - Rich HTML (links, formatting)
    """
    
    _element_type = "dom_text"
    
    def __init__(self, x=0, y=0, w=200, h=50, color=(0, 0, 0, 0), z=0,
                 text="Text", font_size=16, font_family="Arial", text_color=(1, 1, 1, 1), sound_trigger=None):
        """Initialize a DOM text node.
        
        Args:
            x, y: Position coordinates (physics-driven)
            w, h: Width and height dimensions (physics-driven)
            color: RGBA tuple for the rect background (typically transparent)
            z: Z-index for rendering depth
            text: The text content to display
            font_size: Font size in pixels
            font_family: Font family name
            text_color: RGBA tuple (float32, values 0-1) for the text color
            sound_trigger: Sound trigger spec
        """
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._text = text
        self._font_size = font_size
        self._font_family = font_family
        self._text_color = np.array(text_color, dtype=np.float32)

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        """Return fixed target rectangle (static text positioning)."""
        return self.tensor.state.copy()
    
    @property
    def text(self):
        return self._text
    
    @text.setter
    def text(self, value):
        self._text = value
    
    @property
    def font_size(self):
        return self._font_size
    
    @font_size.setter
    def font_size(self, value):
        self._font_size = value
    
    @property
    def font_family(self):
        return self._font_family
    
    @font_family.setter
    def font_family(self, value):
        self._font_family = value
    
    @property
    def text_color(self):
        return self._text_color
    
    @text_color.setter
    def text_color(self, value):
        self._text_color = np.array(value, dtype=np.float32)
    
    @property
    def text_metadata(self):
        """Get text metadata for the JSON metadata bridge."""
        return {
            "type": "dom_text",
            "text": self._text,
            "size": self._font_size,
            "family": self._font_family,
            "color": self._text_color.tolist(),
            "bg_color": self._color.tolist(),
        }

    @property
    def metadata(self):
        """Text metadata for renderer bridge. Overrides DifferentialElement.metadata."""
        return self.text_metadata