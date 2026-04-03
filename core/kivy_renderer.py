"""
Kivy renderer for Aetheris UI - Native Mobile rendering.
Translates AetherEngine's NumPy physics data into Kivy's instruction-based graphics API.

Key challenge: Kivy uses (0,0) bottom-left origin while Aetheris uses (0,0) top-left.
All Y coordinates must be inverted: kivy_y = window_height - element_y - element_height.
"""
import json
import numpy as np
from typing import Union
from core.renderer_base import BaseRenderer


class KivyRenderer(BaseRenderer):
    """Kivy-based renderer for native mobile UI rendering.
    
    This renderer translates physics-driven NumPy arrays into Kivy graphics
    instructions, with hybrid text support (canvas textures for canvas_text,
    actual Label widgets for dom_text).
    """
    
    def __init__(self):
        super().__init__()
        self._canvas = None
        self._text_labels = {}
        self._dom_labels = {}
        self._initialized = False

    def init_window(self, width: int, height: int, title: str = "Aetheris UI") -> None:
        """Initialize the Kivy renderer.
        
        Args:
            width: Window width in pixels
            height: Window height in pixels
            title: Window title
        """
        self._width = width
        self._height = height
        self._title = title
        self._initialized = True

    def set_canvas(self, canvas):
        """Set the Kivy canvas widget for drawing.
        
        Args:
            canvas: Kivy widget with .canvas property
        """
        self._canvas = canvas

    def set_dom_container(self, container):
        """Set the container for DOM-like text labels.
        
        Args:
            container: Kivy widget to hold Label children
        """
        self._dom_container = container

    def clear_screen(self, color: Union[tuple, list, np.ndarray]) -> None:
        """Store background color for rendering.
        
        Args:
            color: RGBA color values (float32, 0-1 range)
        """
        if isinstance(color, np.ndarray):
            self._bg_color = tuple(color)
        else:
            self._bg_color = color

    def _invert_y(self, y: float, h: float) -> float:
        """Convert Aetheris top-left Y to Kivy bottom-left Y.
        
        Args:
            y: Y coordinate in Aetheris space (top-left origin)
            h: Element height
            
        Returns:
            Y coordinate in Kivy space (bottom-left origin)
        """
        return self._height - y - h

    def render_frame(self, data_buffer: np.ndarray, engine_metadata: str = None) -> None:
        """Render a frame from the structured data buffer using Kivy graphics.
        
        Args:
            data_buffer: Structured array from AetherEngine.tick()
            engine_metadata: JSON string from engine.get_ui_metadata()
        """
        if not self._initialized or self._canvas is None or len(data_buffer) == 0:
            return
        
        from kivy.graphics import Color, Rectangle, RoundedRectangle
        from kivy.core.text import Label as CoreLabel
        from kivy.uix.label import Label
        
        rects = data_buffer['rect']
        colors = data_buffer['color']
        z_indices = data_buffer['z']
        n_elements = len(data_buffer)
        
        # Parse metadata
        text_metadata = {}
        if engine_metadata:
            try:
                text_metadata = json.loads(engine_metadata)
            except (json.JSONDecodeError, TypeError):
                text_metadata = {}
        
        # Sort elements by z-index for proper layering
        sorted_indices = sorted(range(n_elements), key=lambda i: int(z_indices[i]))
        
        # Clear canvas instructions (keep only the background)
        self._canvas.clear()
        
        with self._canvas:
            # Background
            bg = getattr(self, '_bg_color', (0.1, 0.1, 0.1, 1.0))
            Color(*bg)
            Rectangle(pos=(0, 0), size=(self._width, self._height))
            
            for i in sorted_indices:
                rect = rects[i]
                color = colors[i]
                z = int(z_indices[i])
                z_key = str(z)
                
                x, y, w, h = float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])
                r, g, b, a = float(color[0]), float(color[1]), float(color[2]), float(color[3])
                
                # Y-axis inversion for Kivy
                kivy_y = self._invert_y(y, h)
                
                # Check if this is a text element
                if z_key in text_metadata:
                    meta = text_metadata[z_key]
                    elem_type = meta.get('type', '')
                    
                    if elem_type == 'canvas_text':
                        # Render text as texture on canvas
                        text = meta.get('text', '')
                        font_size = meta.get('size', 16)
                        font_family = meta.get('family', 'Arial')
                        text_color = meta.get('color', [1.0, 1.0, 1.0, 1.0])
                        
                        # Only draw background if alpha > 0
                        if a > 0.01:
                            Color(r, g, b, a)
                            RoundedRectangle(pos=(x, kivy_y), size=(w, h), radius=[8])
                        
                        # Render text using CoreLabel texture
                        if text:
                            tc_r, tc_g, tc_b, tc_a = text_color[0], text_color[1], text_color[2], text_color[3]
                            core_label = CoreLabel(
                                text=text,
                                font_size=font_size,
                                color=(tc_r, tc_g, tc_b, tc_a),
                            )
                            core_label.refresh()
                            texture = core_label.texture
                            
                            if texture:
                                Color(1, 1, 1, 1)
                                # Center text in the rect
                                text_x = x + (w - texture.size[0]) / 2
                                text_y = kivy_y + (h - texture.size[1]) / 2
                                Rectangle(texture=texture, pos=(text_x, text_y), size=texture.size)
                        
                    elif elem_type == 'dom_text':
                        # Create/update actual Label widget
                        text = meta.get('text', '')
                        font_size = meta.get('size', 16)
                        font_family = meta.get('family', 'Arial')
                        text_color = meta.get('color', [1.0, 1.0, 1.0, 1.0])
                        
                        if z_key not in self._dom_labels:
                            label = Label(
                                text=text,
                                font_size=font_size,
                                color=(text_color[0], text_color[1], text_color[2], text_color[3]),
                                size_hint=(None, None),
                            )
                            if hasattr(self, '_dom_container'):
                                self._dom_container.add_widget(label)
                            self._dom_labels[z_key] = label
                        else:
                            label = self._dom_labels[z_key]
                            label.text = text
                            label.font_size = font_size
                            label.color = (text_color[0], text_color[1], text_color[2], text_color[3])
                        
                        label.pos = (x, kivy_y)
                        label.size = (w, h)
                    else:
                        # Regular element with possible text
                        Color(r, g, b, a)
                        if w > 20 and h > 20:
                            RoundedRectangle(pos=(x, kivy_y), size=(w, h), radius=[8])
                        else:
                            Rectangle(pos=(x, kivy_y), size=(w, h))
                else:
                    # Regular physics element (no text metadata)
                    Color(r, g, b, a)
                    if w > 20 and h > 20:
                        RoundedRectangle(pos=(x, kivy_y), size=(w, h), radius=[8])
                    else:
                        Rectangle(pos=(x, kivy_y), size=(w, h))

    def cleanup_dom_labels(self) -> None:
        """Remove all DOM text labels from the container."""
        if hasattr(self, '_dom_container'):
            for label in self._dom_labels.values():
                if label.parent:
                    label.parent.remove_widget(label)
        self._dom_labels.clear()

    def swap_buffers(self) -> None:
        """No-op for Kivy - canvas updates are immediate."""
        pass

    def draw_rect(self, rect: np.ndarray, color: np.ndarray, z: int) -> None:
        pass

    def draw_rounded_rect(self, rect: np.ndarray, color: np.ndarray, z: int, radius: float) -> None:
        pass

    def draw_text(self, text: str, pos: np.ndarray, size: int, color: np.ndarray) -> None:
        pass
