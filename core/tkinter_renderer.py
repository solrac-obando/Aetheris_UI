"""
Tkinter renderer for Aetheris UI - provides rapid visual prototyping.
Implements the visual contract by receiving structured NumPy arrays from AetherEngine.
"""
import tkinter as tk
from typing import Union
from core.renderer_base import BaseRenderer
import numpy as np


def color_to_hex(color_array: np.ndarray) -> str:
    """Convert [R, G, B, A] float32 (0.0-1.0) to Tkinter hex format #RRGGBB.
    
    Applies linear scaling (Escalamiento Lineal) from Álgebra de Baldor:
    Maps [0.0, 1.0] float32 range to [0, 255] integer range for hex color.
    
    Args:
        color_array: RGBA color values as numpy array with dtype float32, range 0.0-1.0
        
    Returns:
        Hex color string in format #RRGGBB
    """
    # Linear scaling: value_in_new_scale = (value - old_min) * (new_max - new_min) / (old_max - old_min) + new_min
    # For [0.0, 1.0] -> [0, 255]: value_255 = value_float * 255
    r, g, b = [int(x * 255.0) for x in color_array[:3]]  # Ignore alpha for Tkinter hex
    return f'#{r:02x}{g:02x}{b:02x}'


class TkinterRenderer(BaseRenderer):
    """Tkinter-based renderer for rapid prototyping and physics validation.
    
    This renderer implements the BaseRenderer contract using tkinter.Canvas,
    providing immediate visual feedback for debugging the physics solver and
    element asymptote calculations without OpenGL/shader overhead.
    """
    
    def __init__(self):
        """Initialize the Tkinter renderer."""
        super().__init__()
        self._engine = None
        self._root = None
        self._canvas = None
        self._item_tags = {}  # Maps element index to canvas item ID for efficient updates
        self._running = False

    def init_window(self, width: int, height: int, title: str = "Aetheris UI") -> None:
        """Initialize the tkinter window and canvas.
        
        Args:
            width: Window width in pixels
            height: Window height in pixels
            title: Window title
        """
        self._width = width
        self._height = height
        self._title = title
        
        # Create main window
        self._root = tk.Tk()
        self._root.title(title)
        self._root.geometry(f"{width}x{height}")
        
        # Create canvas for drawing
        self._canvas = tk.Canvas(
            self._root,
            width=width,
            height=height,
            bg="black",  # Default background, will be overridden by clear_screen
            highlightthickness=0
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)
        
        # Initialize item tracking
        self._item_tags = {}

    def clear_screen(self, color: Union[tuple, list, np.ndarray]) -> None:
        """Clear the screen with a background color.
        
        Args:
            color: RGBA color values (float32, 0-1 range)
        """
        if self._canvas is None:
            return
            
        # Convert float32 color to Tkinter format
        if isinstance(color, np.ndarray):
            color_tuple = tuple(color)
        else:
            color_tuple = color
            
        hex_color = color_to_hex(np.array(color_tuple[:3], dtype=np.float32))
        self._canvas.configure(bg=hex_color)

    def render_frame(self, data_buffer: np.ndarray) -> None:
        """Render a frame from the structured data buffer.
        
        Optimized version: updates existing canvas items instead of deleting/recreating
        every frame for maximum performance.
        
        Args:
            data_buffer: Structured array from AetherEngine.tick()
                        with dtype [('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')]
        """
        if self._canvas is None:
            return
            
        # Handle empty buffer
        if len(data_buffer) == 0:
            # Clear all items if buffer is empty
            self._canvas.delete("all")
            self._item_tags.clear()
            return
            
        # Process each element in the data buffer
        for i, element_data in enumerate(data_buffer):
            # Extract data from structured array
            rect = element_data['rect']  # [x, y, width, height]
            color = element_data['color']  # [r, g, b, a]
            z = element_data['z']  # z-index (not used in tk renderer but kept for interface)
            
            # Convert coordinates
            x, y, w, h = rect
            x1, y1 = float(x), float(y)
            x2, y2 = float(x + w), float(y + h)
            
            # Convert color to hex
            hex_color = color_to_hex(color)
            
            # Update or create canvas item
            if i in self._item_tags:
                # Update existing item
                item_id = self._item_tags[i]
                self._canvas.coords(item_id, x1, y1, x2, y2)
                self._canvas.itemconfig(item_id, fill=hex_color)
            else:
                # Create new item
                item_id = self._canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=hex_color,
                    outline=""  # No outline for cleaner look
                )
                self._item_tags[i] = item_id
                
        # Remove items for elements that no longer exist
        # (in case elements were unregistered)
        indices_to_remove = []
        for tag_index in self._item_tags:
            if tag_index >= len(data_buffer):
                indices_to_remove.append(tag_index)
                
        for tag_index in indices_to_remove:
            item_id = self._item_tags[tag_index]
            self._canvas.delete(item_id)
            del self._item_tags[tag_index]

    def draw_rect(self, rect: np.ndarray, color: np.ndarray, z: int) -> None:
        """Draw a rectangle.
        
        Note: This method is not used in the optimized render_frame path above,
        but is implemented to satisfy the BaseRenderer abstract contract.
        
        Args:
            rect: [x, y, width, height] in pixel coordinates
            color: RGBA color values (float32, 0-1 range)
            z: Z-index for rendering depth
        """
        # This implementation is provided for completeness but not used in our optimized path
        x, y, w, h = rect
        hex_color = color_to_hex(color)
        if self._canvas:
            self._canvas.create_rectangle(
                x, y, x + w, y + h,
                fill=hex_color,
                outline=""
            )

    def draw_rounded_rect(self, rect: np.ndarray, color: np.ndarray, z: int, radius: float) -> None:
        """Draw a rectangle with rounded corners.
        
        Args:
            rect: [x, y, width, height] in pixel coordinates
            color: RGBA color values (float32, 0-1 range)
            z: Z-index for rendering depth
            radius: Corner radius in pixels
        """
        # Simplified implementation for Tkinter - draws regular rectangle
        # In a full implementation, we'd use create_oval or polygon approximation
        self.draw_rect(rect, color, z)

    def draw_text(self, text: str, pos: np.ndarray, size: int, color: np.ndarray) -> None:
        """Draw text.
        
        Args:
            text: String to render
            pos: [x, y] position in pixel coordinates (baseline)
            size: Font size in pixels
            color: RGBA color values (float32, 0-1 range)
        """
        if self._canvas is None:
            return
            
        x, y = pos
        hex_color = color_to_hex(color)
        if self._canvas:
            self._canvas.create_text(
                x, y,
                text=text,
                fill=hex_color,
                font=("Arial", size),
                anchor="nw"  # Top-left alignment
            )

    def swap_buffers(self) -> None:
        """Finalize the frame and present it to the screen.
        
        In Tkinter, this is handled automatically by the mainloop,
        but we call update_idletasks and update to ensure rendering.
        """
        if self._root:
            self._root.update_idletasks()
            self._root.update()

    def start(self, engine_instance: 'AetherEngine') -> None:
        """Start the Tkinter main loop with physics updates.
        
        Uses root.after(16, self._update) pattern to target 60 FPS (~16ms per frame).
        
        Args:
            engine_instance: The AetherEngine instance to update each frame
        """
        if self._root is None:
            raise RuntimeError("Window must be initialized before calling start()")
            
        self._engine = engine_instance
        self._running = True
        self._update()  # Start the update loop
        self._root.mainloop()  # Start Tkinter event loop

    def _update(self) -> None:
        """Internal update method called repeatedly via root.after().
        
        This implements the main game loop pattern:
        1. Update physics engine
        2. Render frame
        3. Schedule next update
        """
        if not self._running or self._engine is None or self._canvas is None:
            return
            
        try:
            # Update the mathematical engine (physics + asymptote calculation)
            data_buffer = self._engine.tick(self._width, self._height)
            
            # Render using the decoupled renderer
            self.render_frame(data_buffer)
            self.swap_buffers()
            
            # Schedule next update (~60 FPS)
            if self._running:
                self._root.after(16, self._update)
                
        except Exception as e:
            # Handle potential TclError or other issues gracefully
            print(f"Error in TkinterRenderer update loop: {e}")
            self._running = False

    def stop(self) -> None:
        """Stop the renderer loop and cleanup."""
        self._running = False
        if self._root:
            self._root.quit()
            self._root.destroy()

    @property
    def width(self) -> int:
        """Get the current window width."""
        return self._width

    @property
    def height(self) -> int:
        """Get the current window height."""
        return self._height

    @property
    def title(self) -> str:
        """Get the current window title."""
        return self._title